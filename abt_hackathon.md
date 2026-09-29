Round 1 closes tomorrow. The Unstop page says Round 1 runs until 30 Sep 26, 12:00 AM IST. That is the midnight at the start of 30 Sep, so it may already be over. It's 4:56 PM IST on 29 Sep now. The organizer text says "September 30 (Thu)" for the Round 1 deadline, so the two sources disagree. Confirm the exact cutoff in the Discord or WhatsApp group, or by emailing the organizer, Devanshu Saxena. Until you hear back, assume the earlier deadline and submit as soon as you can.

## What the page says

- **Registration:** You're registered. The registration deadline was 22 Sep, and 854 teams have registered.
- **Round 1 (14 Sep to 30 Sep):** Build an Agentic GraphRAG system on TigerGraph. It must answer every question three ways: RAG, GraphRAG and Agentic GraphRAG.
- **Round 1 submission:** A GitHub repo, an architecture diagram, a demo video and a metrics dashboard. The dashboard must show tokens, accuracy and completeness for all three pipelines. A social media post is optional but counts in your favour.
- **Round 2 (1 Oct to 7 Oct):** Only the top 15 teams go through. They extend the agent to handle changing, conflicting and uncertain facts on a harder dataset.
- **Prizes:** ₹35,000 for 1st, ₹20,000 for 2nd and ₹15,000 for 3rd. Everyone with a valid Round 1 submission gets a participation certificate.
- **Date conflict:** The page shows Round 2 results on 7 Oct, but the organizer text says judging is 8 to 10 Oct and results come on 14 Oct.

## Scoring weights

| Criterion | Weight |
|---|---|
| Investigation accuracy | 30% |
| Evidence quality and explainability | 15% |
| Agentic effectiveness and efficiency | 15% |
| Design, engineering and code quality | 15% |
| Innovation | 15% |
| Final presentation and Q&A | 10% |

## Plan for the time left

1. **Get the core working end to end.** Use the provided dataset, and load the graph and vectors into Savanna. Build three pipelines: plain vector RAG, GraphRAG, and an orchestrator agent that picks its next step from the question and the evidence it has so far.
2. **Run the benchmark.** Run every question through all three pipelines. Log tokens, accuracy and completeness, and show the results in a simple dashboard such as Streamlit or a static HTML page.
3. **Show where each approach wins or fails.** The organizers say this comparison is the point, so pick two or three example questions and explain them.
4. **Package the submission.** Write a README that lets someone reproduce your results, and draw the architecture diagram. Record a short demo video, and post about it on social media for the bonus.
5. **Submit early.** Don't leave it to the last minute.

Cut features rather than miss the submission. A working, benchmarked, documented core beats an ambitious build that isn't finished. Temporal reasoning is a stretch goal for Round 2, so skip it for now.

I can also help with a repo structure, the orchestrator agent loop, or GSQL queries.