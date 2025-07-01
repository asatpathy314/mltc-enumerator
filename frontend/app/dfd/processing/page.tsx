"use client";

import { ApiService, DFDRefinementRequest, DFDRefinementResponse } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, Suspense } from "react";

function ProcessingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const dataParam = searchParams.get("data");
  const requestData: DFDRefinementRequest | null = dataParam ? JSON.parse(dataParam) : null;

  // Store the initial request so we can chain later if needed
  useEffect(() => {
    if (requestData) {
      sessionStorage.setItem("dfdRequest", JSON.stringify(requestData));
    }
  }, [requestData]);

  const { data, error, isError } = useQuery<DFDRefinementResponse>({
    queryKey: ["dfd-refine", requestData],
    queryFn: async () => {
      if (!requestData) throw new Error("No request data provided");
      return await ApiService.refineDFD(requestData);
    },
    enabled: !!requestData,
    retry: 1,
  });

  useEffect(() => {
    if (!data) return;

    if (data.message === "need_more_info") {
      sessionStorage.setItem("dfdQuestions", JSON.stringify(data));
      router.push("/dfd/questions");
    } else if (data.message === "success") {
      sessionStorage.setItem("refinedDfd", data.textual_dfd);
      router.push("/dfd/verify");
    }
  }, [data, router]);

  return (
    <div className="flex flex-col items-center justify-center h-[60vh]">
      <div className="text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent mb-6"></div>
        <h2 className="text-2xl font-bold mb-4">Refining your Data-Flow Diagram…</h2>
        {isError && (
          <p className="text-red-500">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        )}
      </div>
    </div>
  );
}

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
    </div>
  );
}

export default function DfdProcessingPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <ProcessingContent />
    </Suspense>
  );
} 