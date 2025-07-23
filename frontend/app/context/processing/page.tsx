"use client";

import { ApiService, ContextEnumeration, EnumerateRequest } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, Suspense } from "react";
import { toast } from "sonner";

function ProcessingContent() {
  const router = useRouter();
  
  // Get request data from sessionStorage instead of URL params
  const requestData: EnumerateRequest = (() => {
    if (typeof window !== 'undefined') {
      const storedRequest = sessionStorage.getItem("contextRequest");
      return storedRequest ? JSON.parse(storedRequest) : null;
    }
    return null;
  })();
  
  // Store the request data in sessionStorage for later use (if not already stored)
  useEffect(() => {
    if (requestData) {
      sessionStorage.setItem("contextRequest", JSON.stringify(requestData));
    } else {
      // If no request data found, redirect back to context page
      toast.error("No request data found. Please submit the form again.");
      router.push("/context");
    }
  }, [requestData, router]);

  const { data, error, isError } = useQuery<ContextEnumeration>({
    queryKey: ["context", requestData],
    queryFn: async () => {
      if (!requestData) {
        throw new Error("No request data provided");
      }
      return await ApiService.enumerateContext(requestData);
    },
    enabled: !!requestData,
    retry: 1,
  });
  
  useEffect(() => {
    if (data) {
      // Store the result in session storage and redirect to results page
      sessionStorage.setItem("contextEnumeration", JSON.stringify(data));
      router.push("/context/results");
    }
    
    if (isError) {
      toast.error("Failed to process context. Please try again.");
    }
  }, [data, isError, router]);

  return (
    <div className="flex flex-col items-center justify-center h-[60vh]">
      <div className="text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite] mb-6"></div>
        <h2 className="text-2xl font-bold mb-4">Processing Your Context</h2>
        <p className="text-muted-foreground mb-8 max-w-md">
          We&apos;re analyzing your data flow diagram to identify attackers, entry points, and assets. This may take 30-60 seconds.
        </p>
        
        {isError && (
          <div className="text-red-500">
            <p>Error: {error instanceof Error ? error.message : "Unknown error"}</p>
            <button 
              onClick={() => router.push("/context")}
              className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200"
            >
              Go Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Loading fallback for the Suspense boundary
function LoadingFallback() {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh]">
      <div className="text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite] mb-6"></div>
        <h2 className="text-2xl font-bold mb-4">Initializing...</h2>
      </div>
    </div>
  );
}

export default function ContextProcessingPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <ProcessingContent />
    </Suspense>
  );
} 