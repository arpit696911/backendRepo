import os
from textwrap import dedent
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from groq import Groq


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Please configure it in your environment.")


client = Groq(api_key=GROQ_API_KEY)


def generate_summary(df: pd.DataFrame) -> str:
    """
    Generate a professional sales insight summary for the given DataFrame.

    The function prepares a textual representation of the dataset along with
    some basic statistics, then sends it to the Groq LLM for analysis.
    """
    # Prepare a compact textual representation of the data without requiring
    # any optional markdown/tabulate dependencies.
    preview_rows = min(len(df), 20)
    preview = df.head(preview_rows).to_string(index=False)

    description_parts: list[str] = []
    description_parts.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    description_parts.append("Columns: " + ", ".join(map(str, df.columns)))

    # Attempt to compute basic numeric stats, but don't fail if there are issues
    try:
        numeric_summary = df.describe(include="all").transpose().to_string()
        description_parts.append("Basic statistics (per column):")
        description_parts.append(numeric_summary)
    except Exception:
        # Fallback if describe() fails for some reason
        pass

    data_text = "\n\n".join(description_parts)

    system_prompt = dedent(
        """
        You are a senior sales analyst. You receive tabular sales data and must generate a clear,
        actionable summary for business stakeholders who are not technical.

        Focus on:
        - Top performing regions or markets
        - Revenue and volume trends over time
        - Product or category performance
        - Customer segments if present
        - Notable anomalies, outliers, or risks
        - 3–5 concise, actionable recommendations

        Use professional, concise language and avoid referencing raw table formatting directly.
        """
    ).strip()

    user_prompt = dedent(
        f"""
        Here is a preview of the sales dataset and some basic statistics.

        High-level dataset info:
        {data_text}

        Preview of the data (first {preview_rows} rows):
        {preview}

        Based on this data, provide a 4–8 paragraph summary plus a short bullet list
        of recommendations at the end.
        """
    ).strip()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=800,
    )

    content: Any = response.choices[0].message.content
    if isinstance(content, str):
        return content.strip()

    # Some clients may return content as a list of parts
    if isinstance(content, list):
        joined = " ".join(str(part) for part in content)
        return joined.strip()

    return str(content).strip()

