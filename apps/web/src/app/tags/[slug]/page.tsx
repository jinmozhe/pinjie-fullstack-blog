import {
  TaxonomyReadingPage,
  taxonomyMetadata,
  type ReadingSearchParams,
} from "@/features/blog";

export const dynamic = "force-dynamic";
type Props = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<ReadingSearchParams>;
};

export async function generateMetadata({ params, searchParams }: Props) {
  return taxonomyMetadata("tags", (await params).slug, await searchParams);
}

export default async function TagPage({ params, searchParams }: Props) {
  return (
    <TaxonomyReadingPage
      kind="tags"
      slug={(await params).slug}
      searchParams={await searchParams}
    />
  );
}
