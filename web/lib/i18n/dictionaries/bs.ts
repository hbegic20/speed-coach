import type { Dictionary } from "./en";

export const bs: Dictionary = {
  metadata: {
    title: "SpeedCoach",
    description:
      "Saznajte zašto je vaša web stranica spora i dobijte jednostavne savjete za svoju platformu.",
    reportTitle: "Izvještaj o brzini",
  },
  header: {
    homeLink: "SpeedCoach početna",
    howItWorks: "Kako radi",
    languageNavigation: "Jezik",
  },
  languageNames: {
    bs: "Bosanski",
    en: "English",
  },
  home: {
    badge: "Besplatna provjera brzine · AI objašnjenja",
    heading: "Saznajte zašto je vaša web stranica spora — i kako tačno da je popravite.",
    lead: "Zalijepite link. Pokrećemo pravu Lighthouse provjeru, a zatim svaki problem objašnjavamo jednostavnim jezikom, s rješenjima za vašu platformu — WordPress, Next.js, Shopify i druge.",
    note: "Bez registracije · Rezultati za otprilike minutu",
    howItWorksHeading: "Kako radi",
    steps: [
      {
        title: "Zalijepite link",
        body: "Bilo koja javna stranica — naslovna, stranica proizvoda ili članak na blogu.",
      },
      {
        title: "Pokrećemo pravu provjeru",
        body: "Google Lighthouse na mobitelu i računaru: brzina, pristupačnost, dobra praksa, SEO i Core Web Vitals.",
      },
      {
        title: "AI vam kaže šta popraviti",
        body: "Najvažnije popravke poredane po uticaju, jednostavno objašnjene, s koracima za platformu na kojoj radi vaša stranica.",
      },
    ],
  },
  form: {
    urlLabel: "Adresa web stranice",
    placeholder: "https://vasa-stranica.ba",
    submit: "Analiziraj",
    rerun: "Ponovi",
    pending: "Pokrećem…",
    errors: {
      invalid_url: "Unesite adresu javne web stranice, na primjer https://primjer.ba.",
      rate_limited: "Pokrenuli ste mnogo provjera u kratkom vremenu. Pokušajte ponovo za nekoliko minuta.",
      site_limit_reached:
        "Već pratite najviše stranica koje besplatni paket dozvoljava. Prestanite pratiti jednu na stranici Moje stranice da biste dodali ovu.",
      unavailable: "Provjeru trenutno nije moguće pokrenuti. Pokušajte ponovo za minutu.",
    },
  },
  report: {
    checkedAt: "Provjereno {date}",
    platform: "Prepoznato: {platform}",
    deviceGroup: "Uređaj",
    devices: { mobile: "Mobitel", desktop: "Računar" },
    scoresLabel: "Ocjene",
    scoreAria: "{label}: ocjena {value} od 100",
    noScore: "Nije izmjereno",
    categories: {
      performance: "Brzina",
      accessibility: "Pristupačnost",
      bestPractices: "Dobra praksa",
      seo: "SEO",
    },
    tones: { good: "Dobro", needsWork: "Treba poboljšati", poor: "Slabo" },
    vitals: {
      heading: "Core Web Vitals",
      subheading: "Ono po čemu Google ocjenjuje iskustvo na stranici",
      largestContentfulPaint: {
        name: "Largest Contentful Paint",
        plain: "Koliko brzo se pojavi glavni sadržaj stranice.",
      },
      totalBlockingTime: {
        name: "Total Blocking Time",
        plain: "Koliko dugo je stranica prezauzeta da reaguje na dodir ili klik.",
      },
      cumulativeLayoutShift: {
        name: "Cumulative Layout Shift",
        plain: "Koliko se sadržaj pomjera dok se stranica učitava.",
      },
      notMeasured: "Nije izmjereno",
    },
    fixes: {
      heading: "Prvo popravite",
      badge: "AI · za {platform}",
      howTo: "Kako popraviti na platformi {platform}",
      howToGeneric: "Kako popraviti",
      saving: "Procijenjena ušteda",
      completion: {
        markDone: "Označi kao urađeno",
        undo: "Poništi",
        done: "Urađeno · ponovite provjeru da potvrdite",
        stillDetected: "I dalje prisutno u ovoj provjeri",
      },
      impact: { high: "Veliki uticaj", medium: "Srednji uticaj", low: "Mali uticaj" },
      none: "Nema ništa važno za popraviti — vaša stranica je u odličnom stanju.",
      unavailable:
        "Savjeti za popravke trenutno nisu dostupni. Vaša mjerenja ispod su spremna.",
    },
    progress: {
      heading: "Provjeravamo vašu stranicu…",
      queued: "Čeka na red",
      running: "Provjera je u toku",
      body: "Pokrećemo Lighthouse na mobitelu i računaru i pišemo vaše popravke. Obično traje oko minutu — ova stranica će se sama osvježiti.",
    },
    failures: {
      heading: "Nismo uspjeli završiti provjeru",
      queue_unavailable: "Naš servis za provjere je trenutno zauzet. Pokušajte ponovo za minutu.",
      site_unreachable:
        "Google nije mogao učitati ovu stranicu. Provjerite da je adresa tačna i da je stranica dostupna.",
      pagespeed_quota_exceeded:
        "Dostigli smo današnje ograničenje provjera brzine. Pokušajte ponovo kasnije.",
      pagespeed_unavailable:
        "Servis za mjerenje brzine trenutno ne odgovara. Pokušajte ponovo za minutu.",
      recommendations_unavailable:
        "Savjeti za popravke trenutno nisu dostupni. Vaša mjerenja ispod su spremna.",
      internal_error: "Nešto je pošlo po zlu kod nas. Pokušajte ponovo.",
    },
  },
  sites: {
    navLink: "Moje stranice",
    metadataTitle: "Moje stranice",
    heading: "Moje stranice",
    subheading: "Praćene stranice provjeravamo automatski svakog ponedjeljka, a svaka provjera se čuva ovdje.",
    addSite: "Dodaj stranicu",
    trackButton: "Prati ovu stranicu",
    stats: {
      averageScore: "Prosječna brzina (mobitel)",
      sinceFirst: "{change} od prve provjere",
      issuesFixed: "Riješeni problemi",
      issuesFixedValue: "{completed} / {total}",
      confirmed: "Potvrđeno zadnjom provjerom: {confirmed}",
      noFixesYet: "Označite popravke kao urađene u izvještaju",
      sitesOfLimit: "{count} od {limit}",
      sitesTracked: "Praćene stranice",
      sitesTrackedNote: "Automatski svakog ponedjeljka, ili kad sami ponovite provjeru",
    },
    chart: {
      heading: "{site} · Brzina",
      subheading: "Ocjena brzine na mobitelu kroz sve provjere",
      siteLabel: "Stranica",
      show: "Prikaži",
      summary: "Brzina na mobitelu se promijenila sa {first} na {latest} (broj provjera: {count})",
      single: "Za sada jedna provjera: brzina na mobitelu {score}",
      empty: "Još nema završenih provjera. Ponovite provjeru da započnete historiju.",
      tableCaption: "Historija provjera",
      date: "Datum",
      score: "Ocjena na mobitelu",
    },
    table: {
      caption: "Praćene stranice",
      site: "Stranica",
      platform: "Platforma",
      performance: "Brzina",
      change: "Promjena",
      lastCheck: "Zadnja provjera",
      actions: "Akcije",
      viewReport: "Pogledaj izvještaj",
      recheck: "Ponovi provjeru",
      remove: "Prestani pratiti",
      notChecked: "Još nije provjereno",
      running: "Provjera je u toku",
      unknownPlatform: "Nepoznato",
    },
    change: {
      up: "Porast: {points}",
      down: "Pad: {points}",
      flat: "Bez promjene",
      none: "Nema dovoljno provjera",
    },
    empty: {
      heading: "Još ne pratite nijednu stranicu",
      body: "Pratite stranicu da sačuvate svaku provjeru i vidite kako se ocjena mijenja nakon popravki.",
    },
    limitReached:
      "Pratite najviše stranica koje besplatni paket dozvoljava ({limit}). Prestanite pratiti jednu da biste dodali drugu.",
    unavailable: "Trenutno ne možemo učitati vaše stranice. Pokušajte ponovo za minutu.",
  },
  notFound: {
    heading: "Izvještaj nije pronađen",
    body: "Ovaj izvještaj ne postoji ili link nije potpun.",
    action: "Provjerite web stranicu",
  },
  footer: {
    builtBy: "Napravio Haris Begić",
  },
};
