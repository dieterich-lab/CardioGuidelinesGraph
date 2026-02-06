from baml_client.sync_client import b 

ollama_host_llm = "10.250.135.153:11430"
output_path = "/prj/doctoral_letters/guide/outputs2/baml_output/MORE_ten_questions_no_rag.txt"

context = """
4.4.1. Appropriate indication for myocardial
revascularization
In CAD patients with moderate or severe inducible ischaemia but no
left main disease nor LVEF of <35%, the largest-to-date ISCHEMIA trial,
up to 5 years, did not show significant benefit of an initial invasive strategy
over an initial conservative strategy for the primary endpoint of ischaemic
cardiovascular events or death from any cause,47 triggering
discussion about the role of initial angiography followed by revascularization
when feasible, in this type of CCS patients, once optimal medical
therapy has been established. The CLARIFY registry found that many
CCS patients with angina experience a resolution of symptoms over
time, often without changes in treatment or revascularization, and experience
good outcomes.404 While these findings suggest that this type
of CCS patients should initially receive conservative medical management,
it is worth noting that patients who were randomly assigned
to the invasive strategy in the ISCHEMIA trial experienced significantly
lower rates of spontaneous MI and greater improvement in
angina-related health status compared with those assigned to the conservative
strategy.47,50 Furthermore, the ORBITA 2 trial demonstrated
that patients with stable angina, who were receiving minimal or no antianginal
medication and had objective evidence of ischaemia, experienced
a lower angina symptom score following PCI treatment
compared with a placebo procedure, indicating a better health status
with respect to angina.52 Although initial conservative medical management
of CCS patients is generally preferred, symptom improvement by
revascularization should therefore not be neglected if patients remain
symptomatic despite antianginal treatment.
After publication of the ISCHEMIA trial results, several meta-
analyses have reported similar overall survival and inevitably higher
rates of procedural MI with routine revascularization, while confirming
consistently greater freedom from spontaneous MI, unstable angina,
and anginal symptoms after revascularization compared with GDMT
alone.732–734 Of note, these meta-analyses showed some differences
in methodology, in selected trials, and follow-up duration.

3470 ESC Guidelines
Furthermore, the importance of ‘any myocardial infarction’ as an endpoint
is complicated by a debate over the prognostic importance of
procedural infarctions as well as how various MI definitions affect the
prediction of long-term outcomes735,736 A more recent meta-analysis
of RCTs that included the longest available follow-up showed that adding
revascularization to GDMT reduced cardiac mortality compared
with GDMT alone. The cardiac survival benefit improved with the duration
of follow-up and was linearly related to a lower rate of spontaneous
MI.55
In ISCHEMIA, patients randomized to initial medical therapy alone had
significantly more spontaneous MIs during the 5-year follow-up, which
were associated with subsequent cardiovascular death.737 An early invasive
strategy was associated with lower long-term risks of cardiovascular
events, mainly spontaneous MIs, compared with a conservative strategy,
at the cost of a higher risk of procedural MIs.738
Extended follow-up of the ISCHEMIA trial population up to 7 years
(ISCHEMIA-EXTEND) revealed a significant 2.2% absolute decrease in
cardiovascular mortality (adjusted HR 0.78; 95% CI, 0.63–0.96) favouring
the initial invasive strategy.56 The benefit was most marked in patients
with multivessel CAD (≥70% diameter stenosis on CCTA;
adjusted HR 0.68; 95% CI, 0.48–0.97) but was offset by a significant
1.2% absolute increase in non-cardiac mortality, without a significant
difference (absolute decrease of −0.7%) in all-cause mortality.56 In a recent
meta-analysis of 18 trials, on the other hand, non-cardiac mortality
did not differ significantly by initial invasive or conservative strategy in
CCS patients with preserved or slightly impaired LVEF.739 In a post
hoc analysis of the ISCHEMIA trial, CAD severity was associated with
a higher risk of all-cause death, MI, and the primary endpoint of the
trial.317 This effect appeared to be most noticeable in patients with multivessel
disease and/or proximal LAD stenosis (≥70% diameter stenosis
on CCTA).
"""

questions = [
    "What was the primary finding of the ISCHEMIA trial regarding invasive versus conservative strategies in CCS patients without left main disease or severely reduced LVEF?",
    "What were the key symptomatic and prognostic benefits of the invasive strategy as reported in ISCHEMIA and ORBITA 2?",
    "How did the ISCHEMIA-EXTEND follow-up influence the interpretation of invasive strategy outcomes, especially in patients with multivessel disease?",
    "Why is 'any myocardial infarction' as an endpoint considered problematic in trial interpretation?",
    "How does the presence of multivessel CAD or proximal LAD stenosis affect the choice between conservative and invasive strategies?",
    "A 62-year-old CCS patient presents with persistent angina despite maximal antianginal therapy and has multivessel disease with 70% proximal LAD stenosis on CCTA. What would a graph-based system infer about the optimal management strategy, and why might standard RAG miss this nuance?",
    "A 58-year-old woman with moderate inducible ischemia, preserved LVEF, and no left main disease has no angina symptoms and prefers non-invasive management. Should she undergo revascularization? What conflicting evidence must be weighed, and how could a Graph RAG clarify this case?",
    "A patient experienced a spontaneous MI two years after choosing conservative management. Based on ISCHEMIA data, what would be the long-term mortality implications, and how can Graph RAG structure this inference better than standard text lookup?",
    "In a patient with mild symptoms, minimal medication, and objective ischemia, would PCI still improve outcomes? How did ORBITA 2 inform this subgroup, and how would a graph-based system assist?",
    "A clinician asks about the trade-off between procedural MI risk and spontaneous MI risk in revascularization. How would Graph RAG resolve this question using multiple studies, and why would standard RAG likely produce fragmented or ambiguous answers?"
]





q_and_a = {}

if __name__ == "__main__":
    for question in questions:
        prompt = question
        q_and_a[prompt]=b.QuestionWithContext(prompt=prompt,context=context)
    print(q_and_a)
    with open(output_path, "w", encoding="utf-8") as f:
        for question, answer in q_and_a.items():
            f.write("Q: " + question.strip() + "\n")
            f.write("A: " + str(answer).strip() + "\n\n")