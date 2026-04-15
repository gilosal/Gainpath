import { redirect } from "next/navigation";

// Root redirect → Today view
export default function Home() {
  redirect("/today");
}
