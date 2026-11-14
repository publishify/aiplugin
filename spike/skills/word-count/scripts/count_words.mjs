// Counts words and characters of a txt or md file. Prints one JSON line, no text from the file.
import { readFileSync } from "node:fs";

const path = process.argv[2];
if (path.toLowerCase().endsWith(".docx")) {
  console.log(JSON.stringify({ language: "javascript", error: "docx needs the Python script" }));
} else {
  const text = readFileSync(path, "utf8");
  const words = text.match(/[\p{L}\p{N}_]+/gu)?.length ?? 0;
  console.log(JSON.stringify({ language: "javascript", words, characters: text.length }));
}
