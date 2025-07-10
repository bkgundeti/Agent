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

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ Load MongoDB configuration
mongo_uri = os.getenv("MONGO_URI")
mongo_db_name = os.getenv("MONGO_DB_NAME")
mongo_collection_name = os.getenv("MONGO_COLLECTION_NAME")

if not all([mongo_uri, mongo_db_name, mongo_collection_name]):
    raise ValueError("❌ MongoDB environment variables not set correctly in .env file.")

# ✅ Connect to MongoDB Atlas
mongo_client = MongoClient(mongo_uri)
db = mongo_client[mongo_db_name]
user_inputs_collection = db[mongo_collection_name]
print("✅ Connected to MongoDB Atlas")

# ✅ Load Azure OpenAI credentials
api_key = os.getenv("AZURE_OPENAI_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
assistant_id = os.getenv("AZURE_OPENAI_ASSISTANT_ID")

if not all([api_key, azure_endpoint, deployment_name]):
    raise ValueError("❌ Azure OpenAI environment variables not set correctly.")

# ✅ Initialize GPT client
gpt_client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-05-01-preview",
    azure_endpoint=azure_endpoint,
    default_headers={"azure-openai-deployment": deployment_name}
)

# ✅ Graceful server shutdown flag
should_exit = False

def shutdown_server():
    print("\n❌ User entered 'exit'. Shutting down server...")
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
                return render_template("index.html", output="⚠️ Please enter both Username and Requirement.")

            if requirement.strip().lower() in ["exit", "quit"]:
                should_exit = True
                shutdown_server()
                return "<h3>❌ Server shutting down as per user request...</h3>"

            # Step 1: Analyze input using Chat Agent
            chat_agent = ChatAgent(gpt_client)
            chat_response = chat_agent.process_web_input(requirement)

            if not chat_response:
                output = "⚠️ Sorry, could not understand your input."
                return render_template("index.html", output=output, username=username, requirement=requirement)

            # ✅ If it's not a model use-case, reply only (chat mode)
            if not chat_response["proceed"]:
                output = chat_response["message"]
                return render_template("index.html", output=output, username=username, requirement=requirement)

            # ✅ Otherwise: Run full recommendation pipeline
            analyzed_input = chat_response["message"]

            # Step 2: Recommend Models
            recommender_agent = RecommenderAgent(gpt_client)
            recommended_models = recommender_agent.recommend_models(analyzed_input)

            # Step 3: Analyze Pricing
            pricing_agent = PricingAgent(assistant_id, api_key, azure_endpoint)
            pricing_table = pricing_agent.analyze_pricing(recommended_models)

            # Step 4: Generate Final Report
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
            print(f"❌ FULL ERROR: {e}")
            output = f"❌ Error: {str(e)}"

    return render_template("index.html", output=output, username=username, requirement=requirement)

# ✅ Run Flask server
if __name__ == "__main__":
    print("✅ Flask app is starting on http://localhost:5000")
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n❌ Server shutdown complete.")
        sys.exit(0)
