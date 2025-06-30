import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PlusCircle, X, Save } from "lucide-react";

interface EditableAssumptionsListProps {
  assumptions: string[];
  onAssumptionsChange: (updatedAssumptions: string[]) => void;
}

export default function EditableAssumptionsList({
  assumptions,
  onAssumptionsChange,
}: EditableAssumptionsListProps) {
  // Local copy for editing
  const [editingAssumptions, setEditingAssumptions] = useState<string[]>(assumptions);
  const [isEditing, setIsEditing] = useState(false);

  if (!assumptions || assumptions.length === 0) {
    return (
      <div className="space-y-4">
        <Alert>
          <AlertDescription>No assumptions identified.</AlertDescription>
        </Alert>
        <Button className="flex gap-2 items-center" onClick={() => handleAddAssumption()}>
          <PlusCircle size={16} /> Add Assumption
        </Button>
      </div>
    );
  }

  const handleAssumptionChange = (index: number, value: string) => {
    const updatedAssumptions = [...editingAssumptions];
    updatedAssumptions[index] = value;
    setEditingAssumptions(updatedAssumptions);
  };

  const handleAddAssumption = () => {
    const updatedAssumptions = [...editingAssumptions, "New assumption"];
    setEditingAssumptions(updatedAssumptions);
    setIsEditing(true);
  };

  const handleRemoveAssumption = (index: number) => {
    const updatedAssumptions = [...editingAssumptions];
    updatedAssumptions.splice(index, 1);
    setEditingAssumptions(updatedAssumptions);
  };

  const handleSaveChanges = () => {
    onAssumptionsChange(editingAssumptions);
    setIsEditing(false);
  };

  const handleCancelChanges = () => {
    setEditingAssumptions(assumptions);
    setIsEditing(false);
  };

  return (
    <Card>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Assumptions</CardTitle>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button size="sm" variant="outline" onClick={handleCancelChanges}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleSaveChanges} className="flex items-center gap-1">
                <Save size={16} /> Save
              </Button>
            </>
          ) : (
            <Button size="sm" variant="outline" onClick={() => setIsEditing(true)}>
              Edit Assumptions
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        {isEditing ? (
          <div className="space-y-2">
            {editingAssumptions.map((assumption, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  value={assumption}
                  onChange={(e) => handleAssumptionChange(index, e.target.value)}
                  placeholder="Enter assumption"
                  className="flex-1"
                />
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="icon"
                  onClick={() => handleRemoveAssumption(index)}
                >
                  <X size={16} />
                </Button>
              </div>
            ))}
            
            <div className="mt-4">
              <Button className="flex gap-2 items-center" onClick={handleAddAssumption} variant="outline">
                <PlusCircle size={16} /> Add Assumption
              </Button>
            </div>
          </div>
        ) : (
          <ul className="list-disc pl-5 space-y-1">
            {editingAssumptions.map((assumption, index) => (
              <li key={index}>{assumption}</li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
} 