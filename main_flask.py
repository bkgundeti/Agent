from flask import Flask, request, render_template
from pymongo import MongoClient
import os
import signal
import sys
from dotenv import load_dotenv

from openai import AzureOpenAI
from agents.chat_agent import ChatAgent
from agents.requir_recommender_agent import RecommenderAgent
from agents.pricing_agent import PricingAgent
from agents.report_agent import ReportAgent

# ✅ Load .env File
load_dotenv()

# ✅ Flask App Init
app = Flask(__name__)

# ✅ Load Environment Variables
mongo_uri = os.getenv("MONGO_URI")
mongo_db_name = os.getenv("MONGO_DB_NAME")
mongo_collection_name = os.getenv("MONGO_COLLECTION_NAME")

# ✅ Validate MongoDB Vars
if not all([mongo_uri, mongo_db_name, mongo_collection_name]):
    raise ValueError("❌ MongoDB environment variables not set correctly in .env file.")

# ✅ Connect to MongoDB
mongo_client = MongoClient(mongo_uri)
db = mongo_client[mongo_db_name]
user_inputs_collection = db[mongo_collection_name]
print("\u2705 Connected to MongoDB Atlas")

# ✅ Azure OpenAI Setup
api_key = os.getenv("AZURE_OPENAI_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
assistant_id = os.getenv("AZURE_OPENAI_ASSISTANT_ID")

if not all([api_key, azure_endpoint, deployment_name]):
    raise ValueError("❌ Azure OpenAI environment variables not set correctly.")

gpt_client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-05-01-preview",
    azure_endpoint=azure_endpoint,
    default_headers={"azure-openai-deployment": deployment_name}
)

# ✅ Graceful Shutdown
should_exit = False

def shutdown_server():
    print("\n\u274C User entered 'exit'. Shutting down server...")
    os.kill(os.getpid(), signal.SIGINT)

# ✅ Flask Route
@app.route("/", methods=["GET", "POST"])
def index():
    global should_exit
    output = None
    username = None
    requirement = None

    if request.method == "POST":
        try:
            username = request.form.get("username")
            requirement = request.form.get("requirement")

            if not username or not requirement:
                return render_template("index.html", output="\u26A0\uFE0F Please enter both Username and Requirement.")

            if requirement.strip().lower() in ["exit", "quit"]:
                should_exit = True
                shutdown_server()
                return "<h3>\u274C Server shutting down as per user request...</h3>"

            # Step 1: Analyze
            chat_agent = ChatAgent(gpt_client)
            analyzed_input = chat_agent.process_web_input(requirement)

            if not analyzed_input:
                output = "\u274C Irrelevant input. Please enter a proper AI-related requirement (e.g., chatbot, summarization, detection, etc.)."
                return render_template("index.html", output=output, username=username, requirement=requirement)

            # Step 2: Recommend
            recommender_agent = RecommenderAgent(gpt_client)
            recommended_models = recommender_agent.recommend_models(analyzed_input)

            # Step 3: Pricing
            pricing_agent = PricingAgent(assistant_id, api_key, azure_endpoint)
            pricing_table = pricing_agent.analyze_pricing(recommended_models)

            # Step 4: Final Report
            report_agent = ReportAgent(gpt_client)
            final_output = report_agent.generate_report(analyzed_input, recommended_models, pricing_table)

            # Step 5: Save to MongoDB
            user_inputs_collection.insert_one({
                "username": username,
                "requirement": requirement,
                "analyzed_input": analyzed_input,
                "recommended_models": recommended_models,
                "pricing_table": pricing_table,
                "final_output": final_output
            })

            output = final_output

        except Exception as e:
            print(f"\u274C FULL ERROR: {e}")
            output = f"\u274C Error: {str(e)}"

    return render_template("index.html", output=output, username=username, requirement=requirement)

# ✅ Run the Flask App
if __name__ == "__main__":
    print("\u2705 Flask app is starting on http://localhost:5000")
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n\u274C Server shutdown complete.")
        sys.exit(0)
