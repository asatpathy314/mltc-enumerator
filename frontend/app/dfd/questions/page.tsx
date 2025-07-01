"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiService, DFDRefinementRequest } from "@/lib/api";
import EditableQuestionsList from "@/components/editable-questions-list";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function DfdQuestionsPage() {
  const router = useRouter();
  const [request, setRequest] = useState<DFDRefinementRequest | null>(null);
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);

  useEffect(() => {
    const stored = sessionStorage.getItem("dfdQuestions");
    const reqStored = sessionStorage.getItem("dfdRequest");
    if (!stored || !reqStored) {
      router.push("/dfd");
      return;
    }
    const data = JSON.parse(stored);
    setQuestions(data.questions || []);
    setAnswers(Array(data.questions.length).fill(""));
    const req = JSON.parse(reqStored);
    setRequest(req);
  }, [router]);

  const handleQAChange = (qs: string[], ans: string[]) => {
    setQuestions(qs);
    setAnswers(ans);
  };

  const handleSubmit = async () => {
    if (!request) return;
    const newRequest: DFDRefinementRequest = {
      textual_dfd: request.textual_dfd,
      questions,
      answers,
    };
    try {
      sessionStorage.setItem("dfdRequest", JSON.stringify(newRequest));
      const res = await ApiService.refineDFD(newRequest);
      if (res.message === "need_more_info") {
        sessionStorage.setItem("dfdQuestions", JSON.stringify(res));
        router.refresh();
      } else {
        sessionStorage.setItem("refinedDfd", res.textual_dfd);
        router.push("/dfd/verify");
      }
    } catch (e) {
      toast.error("Failed to submit answers");
      console.error(e);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Answer Clarifying Questions</h1>
      <EditableQuestionsList questions={questions} answers={answers} onQAChange={handleQAChange} />
      <div className="flex justify-end">
        <Button onClick={handleSubmit}>Submit Answers</Button>
      </div>
    </div>
  );
} 