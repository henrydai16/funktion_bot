import discord
import asyncio
import ollama
import os
from discord.ext import commands
import glob
import numpy as np
import re
import pickle


class Ask(commands.Cog):
    def __init__(self, bot):
        # Calls when loading cog
        self.bot = bot

        # In-memory RAG storage
        self.index = []
        self.embeddings = None

        # Move RAG persistence into data/ folder
        self.embed_path = "data/embeddings.npy"
        self.chunk_path = "data/chunks.pkl"

        # Ensure data folder exists
        if not os.path.exists("data"):
            os.makedirs("data")

        # Build or load RAG index on startup
        self.load_or_build_index()

    def load_and_chunk(self, path="data/*.md", max_tokens=800, overlap_tokens=300):
        """
        Header-aware + paragraph + sentence chunking
        with token-based sliding window overlap.
        """

        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")

        chunks = []

        for file in glob.glob(path):
            with open(file, "r", encoding="utf-8") as f:
                text = f.read()

            # 1. Split by headers first (preserve structure)
            sections = re.split(r"(?=^#+\s)", text, flags=re.MULTILINE)

            for section in sections:
                section = section.strip()
                if len(section) < 50:
                    continue

                # 2. Split into paragraphs
                paragraphs = section.split("\n\n")

                buffer = []
                buffer_tokens = 0

                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue

                    # 3. sentence split (lightweight)
                    sentences = re.split(r"\n|(?<=[.!?])\s+", para)
                
                    for sent in sentences:
                        if len(sent.strip()) < 2:
                            continue
                        tokens = len(enc.encode(sent))

                        # if adding exceeds limit → flush chunk
                        if buffer_tokens + tokens > max_tokens:
                            chunks.append({
                                "text": " ".join(buffer),
                                "source": file,
                                "section": section[:80]
                            })

                            # overlap: keep last ~300 tokens
                            overlap_text = " ".join(buffer)
                            overlap_tokens_count = len(enc.encode(overlap_text))

                            if overlap_tokens_count > overlap_tokens:
                                overlap_sentences = buffer[-3:]
                            else:
                                overlap_sentences = buffer

                            buffer = overlap_sentences.copy()
                            buffer_tokens = len(enc.encode(" ".join(buffer)))

                        buffer.append(sent)
                        buffer_tokens += tokens

                # flush remainder
                if buffer:
                    chunks.append({
                        "text": " ".join(buffer),
                        "source": file,
                        "section": section[:80]
                    })

        return chunks

    # -------------------------------------------------
    # EMBEDDING FUNCTION (Ollama)
    # -------------------------------------------------
    def embed(self, text):
        """
        Converts text → vector embedding using nomic-embed-text model.
        This is what enables semantic search instead of keyword matching.
        """

        return ollama.embeddings(
            model="nomic-embed-text",
            prompt=text
        )["embedding"]

    # -------------------------------------------------
    # BUILD INDEX (RUN ON FIRST SETUP)
    # -------------------------------------------------
    def build_index(self, chunks):
        """
        Converts all chunks into embeddings and stores them in memory.
        This is the core RAG indexing step.
        """

        self.index = []
        embeddings = []

        for chunk in chunks:
            # DEBUG: check chunk size BEFORE embedding
            print("Chunk size:", len(chunk["text"]))
            vec = self.embed(chunk["text"])

            self.index.append(chunk)
            embeddings.append(vec)

        self.embeddings = np.array(embeddings)
        self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)

    # -------------------------------------------------
    # SAVE EMBEDDINGS + CHUNKS (PERSISTENCE)
    # -------------------------------------------------
    def save_index(self):
        """
        Saves embeddings + chunks into data/ folder.
        """

        np.save(self.embed_path, self.embeddings)

        with open(self.chunk_path, "wb") as f:
            pickle.dump(self.index, f)

    # -------------------------------------------------
    # LOAD EMBEDDINGS + CHUNKS
    # -------------------------------------------------
    def load_index(self):
        """
        Loads embeddings + chunks from data/ folder.
        """

        self.embeddings = np.load(self.embed_path, allow_pickle=True)
        self.embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        with open(self.chunk_path, "rb") as f:
            self.index = pickle.load(f)

    # -------------------------------------------------
    # INIT LOGIC (DECIDES LOAD VS BUILD)
    # -------------------------------------------------
    def load_or_build_index(self):
        if os.path.exists(self.embed_path) and os.path.exists(self.chunk_path):
            print("Loading saved RAG index...")
            self.load_index()
        else:
            print("Building RAG index...")
            chunks = self.load_and_chunk()
            self.build_index(chunks)
            self.save_index()

    # -------------------------------------------------
    # RETRIEVAL FUNCTION (CORE RAG LOGIC)
    # -------------------------------------------------
    def retrieve_context(self, query, k=8):
        """
        1. Embed query
        2. Compare to all chunk embeddings
        3. Retrieve top-k most similar chunks
        """

        query_vec = self.embed(query)

        # cosine-like similarity (dot product works best if vectors are normalized)
        query_vec = query_vec / np.linalg.norm(query_vec)
        scores = np.dot(self.embeddings, query_vec)

        top_k_idx = np.argsort(scores)[::-1][:k]

        results = []

        for i in top_k_idx:
            chunk = self.index[i]

            score = scores[i]

            # entity boost (simple fix for your problem)
            if "enCore" in chunk["text"]:
                score += 0.05

            results.append((score, chunk))

        # re-rank after boosting
        results.sort(key=lambda x: x[0], reverse=True)

        return "\n\n".join(
            f"[Source: {c['source']}]\n"
            f"[Section: {c.get('section','')}] \n"
            f"{c['text']}"
            for _, c in results
        )

    # -------------------------------------------------
    # DISCORD COMMAND
    # -------------------------------------------------
    @commands.command(
        brief="Ask FunKtion history via: !ask '[prompt]'",
        help="Uses RAG over FunKtion markdown archives to answer questions"
    )
    async def ask(self, ctx):
        """
        Main user-facing command.
        Combines:
        - retrieved context (RAG)
        - LLM reasoning (Ollama)
        """

        model = "qwen3:14b"

        system_prompt = """
        You are a helpful assistant for FunKtion (University of Michigan dance team).
        Use provided context if relevant.
        If context is not relevant, answer normally.
        """

        # Extract user query after !ask
        prompt = ctx.message.content[len(ctx.prefix + "ask "):].strip()

        if not prompt:
            await ctx.send("Ask me something after !ask")
            return

        # Retrieve relevant chunks (THIS is the RAG step)
        context = self.retrieve_context(prompt)

        # Combine retrieved knowledge + user question
        full_prompt = f"""
### Context
{context}

### User Question
{prompt}
"""

        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt},
            ],
        )

        content = response["message"]["content"]

        # Discord message limit handling (2000 chars)
        for i in range(0, len(content), 1900):
            await ctx.send(f"{ctx.author.mention} {content[i:i+1900]}")


async def setup(bot):
    await bot.add_cog(Ask(bot))