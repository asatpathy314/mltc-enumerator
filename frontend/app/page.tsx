import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-8">
      <section className="text-center mb-16">
        <h1 className="text-4xl font-bold mb-4">MLTC Enumerator</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          A tool for security threat modeling and analysis using machine learning techniques
        </p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Context Enumeration</CardTitle>
            <CardDescription>
              Identify attackers, entry points, and assets from a data flow diagram
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              Provide a textual description of your system&apos;s data flow diagram and get an automated analysis
              of potential security threats.
            </p>
            <div className="flex justify-end">
              <Button asChild>
                <Link href="/dfd">Start Enumeration</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Threat Chains</CardTitle>
            <CardDescription>
              Generate comprehensive threat chains based on verified context
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              After reviewing and verifying the context enumeration, generate detailed threat chains
              showing how attackers could exploit entry points to compromise assets.
            </p>
            <div className="flex justify-end">
              <Button asChild>
                <Link href="/threats">View Threats</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
