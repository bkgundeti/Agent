import json
from openai import AzureOpenAI
from agents.logger import get_logger

logger = get_logger("report_agent", "logs/report_agent.log")

class ReportAgent:
    def __init__(self, gpt_client):
        self.client = gpt_client
        logger.info("Report Agent initialized using GPT directly (no assistant)")

    def generate_report(self, analyzed_input, recommended_models, pricing_table):
        logger.info("Sending all inputs to GPT for final analysis...")

        prompt = f"""
You are an expert AI model selector.

Input:
1. Analyzed user requirement:
\"\"\"{analyzed_input}\"\"\"

2. Recommended models:
\"\"\"{recommended_models}\"\"\"

3. Pricing details of shortlisted models:
\"\"\"{pricing_table}\"\"\"

Task:
- Analyze all information and intelligently select the best model based on accuracy, speed, and relevance to user need.
- Keep cost in mind, but prioritize user needs.

Important:
- Output MUST follow this **exact plain format**:

Final Best Model Recommended:
1. Model Name      : <model_name>
2. Price           : <price with unit>
3. Speed           : <speed>
4. Accuracy        : <accuracy>
5. Cloud           : <provider>
6. Region          : <region>
7. Reason for Selection : <short, neat, clear reason>

Guidelines:
- Don't use asterisks, markdown, or bullet points.
- Ensure output looks clean, beautiful, and readable for end-users.
- Use fixed spacing after each colon for visual alignment.
- If some information is missing, write "Not specified" and continue.
- Keep the reason one short sentence only.
"""

        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a smart assistant helping select the best AI model with a beautiful plain format output."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=700
            )

            result = completion.choices[0].message.content.strip()
            logger.info("GPT response generated successfully.")
            return result

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"
