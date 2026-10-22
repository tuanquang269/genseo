# What to ask next

Blog articles only. This block is a cluster follow-up list. It is not an FAQ.

Place it in the markdown before `## Frequently Asked Questions`. The publisher builds FAQ schema only from that FAQ heading and its `###` questions. This block uses a normal H2 and markdown links, so it does not add a second FAQ schema node.

Generate it when `state/cluster_map.json` exists:

```bash
python3 scripts/cluster_related_questions.py --query "<primary keyword>" --package
python3 scripts/cluster_related_questions.py --handle <article-handle> --package
```

`--package` prints the in-body sentences (pillar plus 2 to 4 siblings when they exist) and then the question list. `--query` is for a draft whose handle is not in the map yet. If the map file is missing, the command prints a one-line note and exits 0. The daily publisher does not require the block.

Rules:

- 3 to 5 questions when the cluster has enough siblings. Fewer is allowed when the cluster is small.
- Each question links to the sibling article that answers it (or the pillar).
- Anchor text is the question. Do not paste a footer list with no sentence around the in-body cluster links. Those sentences come from `scripts/cluster_internal_links.py`.
- Do not invent a dose, a study result, or a product that is not ShilaSource Himalayan Shilajit Resin, AgeAura Pure NMN + TMG (`/products/ageaura-pure-nmn-tmg-nad-complex`), or FloraFresh (Bacillus coagulans SNZ-1969, 15B CFU per 2 gummies).
- Do not use `gsl-*` or landing-page URLs.

HTML equivalent used by backfill (marker `data-genseo-cluster-link`):

```html
<section class="genseo-related-questions" data-genseo-cluster-link="related-questions">
  <h2>What to ask next</h2>
  <p>These questions link to other articles in the same cluster. They are follow-ups, not a second FAQ.</p>
  <ul>
    <li><a data-genseo-cluster-link="next-HANDLE" href="https://wellnessnest.co/blogs/news/HANDLE">Question?</a></li>
  </ul>
</section>
```
