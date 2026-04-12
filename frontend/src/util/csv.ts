import { importStudentsForCourse } from "./api";

  export const importCSV = (id: string | number) => {
    // Prompt the user to select a file
    const input = document.createElement("input");
    input.setAttribute("type", "file");
    input.setAttribute("accept", ".csv");

    // Handle the file selection event
    input.addEventListener("change", async () => {
      const file = input.files?.[0];
      const reader = new FileReader();

      reader.onload = async () => {
        const text = reader.result?.toString();

        if (!text) {
          alert("Please select a file to upload");
          return;
        }

        try {
          await importStudentsForCourse(Number(id), text);
          alert("Students enrolled successfully! Refresh the Members tab to see them.");
        } catch (error) {
          alert("Error enrolling students: " + error + "\n\nMake sure your CSV has columns: id, name, email");
        }
      };

      if (!file) {
        alert("Please select a file to upload");
        return;
      }

      reader.readAsText(file);
    });

    input.click();
  };
