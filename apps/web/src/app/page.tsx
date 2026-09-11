import {
  HomeReadingPage,
  homeMetadata,
  type ReadingSearchParams,
} from "@/features/blog";

export const dynamic = "force-dynamic";
type Props = { searchParams: Promise<ReadingSearchParams> };

export async function generateMetadata({ searchParams }: Props) {
  return homeMetadata(await searchParams);
}

export default async function HomePage({ searchParams }: Props) {
  return <HomeReadingPage searchParams={await searchParams} />;
}
