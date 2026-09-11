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
  return taxonomyMetadata(
    "categories",
    (await params).slug,
    await searchParams,
  );
}

export default async function CategoryPage({ params, searchParams }: Props) {
  return (
    <TaxonomyReadingPage
      kind="categories"
      slug={(await params).slug}
      searchParams={await searchParams}
    />
  );
}
