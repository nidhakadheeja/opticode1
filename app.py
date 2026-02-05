from flask import Flask, render_template, request, jsonify
import os
import ast
from dotenv import load_dotenv

# -----------------------------
# LOAD ENV VARIABLES FIRST
# -----------------------------
load_dotenv()
print("GROQ KEY LOADED:", os.getenv("GROQ_API_KEY"))

app = Flask(__name__)

# -----------------------------
# IMPORT OPTIMIZERS
# -----------------------------
from optimizer.rule_optimizer import run_rule_optimizer
from optimizer.llm_optimizer import optimize_with_groq, parse_llm_response


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------
# LEVEL 1 OPTIMIZATION
# -----------------------------
@app.route("/optimize/level1", methods=["POST"])
def optimize_level1():
    data = request.get_json()
    code = data.get("code", "")

    try:
        optimized_code, explanations = run_rule_optimizer(code)

        return jsonify({
            "optimized_code": optimized_code,
            "explanation": "\n".join(explanations),
            "complexity_before": "N/A",
            "complexity_after": "Improved"
        })

    except Exception as e:
        return jsonify({
            "optimized_code": "",
            "explanation": f"Level 1 optimization failed: {str(e)}",
            "complexity_before": "N/A",
            "complexity_after": "N/A"
        })


# -----------------------------
# LEVEL 2 OPTIMIZATION (LLM)
# -----------------------------
@app.route("/optimize/level2", methods=["POST"])
def optimize_level2():
    data = request.get_json()
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "No code provided"}), 400

    # Syntax safety check
    try:
        ast.parse(code)
    except SyntaxError as e:
        return jsonify({
            "optimized_code": "",
            "explanation": f"Syntax Error: {str(e)}",
            "complexity_before": "N/A",
            "complexity_after": "N/A"
        })

    try:
        llm_output = optimize_with_groq(code)

        print("\n--- RAW LLM OUTPUT ---\n")
        print(llm_output)

        optimized_code, explanation_list = parse_llm_response(llm_output)

        return jsonify({
            "optimized_code": optimized_code,
            "explanation": "\n".join(explanation_list),
            "complexity_before": "Estimated",
            "complexity_after": "Improved (LLM-based)"
        })

    except Exception as e:
        return jsonify({
            "optimized_code": "",
            "explanation": f"Level 2 optimization failed: {str(e)}",
            "complexity_before": "N/A",
            "complexity_after": "N/A"
        })


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
