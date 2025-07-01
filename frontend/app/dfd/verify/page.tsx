"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export default function DfdVerifyPage() {
  const router = useRouter();
  const [dfd, setDfd] = useState<string>("");

  useEffect(() => {
    const stored = sessionStorage.getItem("refinedDfd");
    if (!stored) {
      router.push("/dfd");
      return;
    }
    setDfd(stored);
  }, [router]);

  const handleContinue = () => {
    // store refined DFD for context stage
    sessionStorage.setItem("contextPrefillDfd", dfd);
    router.push("/context");
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold mb-4">Verify Refined DFD</h1>
      <Textarea className="min-h-[300px]" value={dfd} readOnly />
      <div className="flex justify-end gap-4">
        <Button variant="secondary" onClick={() => router.push("/dfd/questions")}>Back</Button>
        <Button onClick={handleContinue}>Looks Good</Button>
      </div>
    </div>
  );
} 