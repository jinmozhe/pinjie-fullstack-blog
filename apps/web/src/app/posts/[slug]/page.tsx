import { ArticleReadingPage, articleMetadata } from "@/features/blog";

export const dynamic = "force-dynamic";
type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props) {
  return articleMetadata((await params).slug);
}

export default async function PostPage({ params }: Props) {
  return <ArticleReadingPage slug={(await params).slug} />;
}
