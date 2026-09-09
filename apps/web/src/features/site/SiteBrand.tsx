import type { SiteProfileRead } from "@pinjie/api-client";
import Image from "next/image";
import Link from "next/link";

import { DEFAULT_SITE_PROFILE } from "./profile";

export function SiteBrand({
  profile = DEFAULT_SITE_PROFILE,
}: {
  profile?: Pick<SiteProfileRead, "name" | "logo_url">;
}) {
  return (
    <Link className="site-brand wordmark" href="/" aria-label={`${profile.name}首页`}>
      {profile.logo_url ? (
        <Image
          className="site-brand__logo"
          src={profile.logo_url}
          alt=""
          aria-hidden="true"
          width={32}
          height={32}
          unoptimized
        />
      ) : null}
      <span>{profile.name}</span>
    </Link>
  );
}
