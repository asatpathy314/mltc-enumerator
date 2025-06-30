import { useState, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface EditContextItemProps {
  title: string;
  description?: string;
  onSave: () => void;
  onCancel: () => void;
  onDelete?: () => void;
  viewMode: ReactNode;
  editMode: ReactNode;
}

export default function EditContextItem({
  title,
  description,
  onSave,
  onCancel,
  onDelete,
  viewMode,
  editMode,
}: EditContextItemProps) {
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = () => {
    onSave();
    setIsEditing(false);
  };

  const handleCancel = () => {
    onCancel();
    setIsEditing(false);
  };

  return (
    <Card>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg">{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button size="sm" variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave}>
                Save
              </Button>
            </>
          ) : (
            <>
              <Button size="sm" variant="outline" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
              {onDelete && (
                <Button size="sm" variant="destructive" onClick={onDelete}>
                  Delete
                </Button>
              )}
            </>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isEditing ? editMode : viewMode}
      </CardContent>
    </Card>
  );
} 