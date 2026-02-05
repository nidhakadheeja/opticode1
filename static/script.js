async function optimizeCode() {
    const code = document.getElementById("codeInput").value;
    const level = document.querySelector('input[name="level"]:checked').value;

    if (!code.trim()) {
        alert("Please enter Python code");
        return;
    }

    const response = await fetch(`/optimize/${level}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: code })
    });

    const data = await response.json();

    document.getElementById("optimizedCode").innerText =
        data.optimized_code || "Optimization failed";

    document.getElementById("explanation").innerText =
        data.explanation || "No explanation";

    document.getElementById("before").innerText =
        data.complexity_before || "N/A";

    document.getElementById("after").innerText =
        data.complexity_after || "N/A";
}
