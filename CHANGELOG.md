# Changelog

## 2.1.1 — 2026-11-06

Correctif : filet or des titres en thème clair.

### Contenu

- **Filet or en clair** : `--color-title-rule` prend la valeur `accent` de la charte v2.1 (`#8F6300` en clair, 5,31:1 sur `surface`) au lieu de `accent-aplat` (`#E0B54A`, 1,9:1). Le sombre est inchangé (`#E3C26B`). `DESIGN.md` et `tests/test_web_tokens.py` réalignés (valeur par thème, contraste 3:1 sur `surface` et `surface-raised` dans les deux thèmes).
- **Captures** : `docs/media/charte-v2/` refaites en clair pour les pages à filet (LLM, RAG, MCP, Sécurité, Modèles), diagnostic terminé et modèle choisi.

### Limites

- Les captures sont prises sur la pile e2e (faux modèle cloud, réseau coupé) : l'avertissement « réseau » du diagnostic y est normal.

## 2.1.0 — 2026-11-06

Migration de l'interface vers la charte générique v2.1 (sombre d'abord, jetons choisis par usage).

### Contenu

- **Thèmes** : le sombre est le thème par défaut (`:root` de `tokens.css`) ; le clair sous `[data-theme="light"]` et sous `prefers-color-scheme: light` quand aucun thème n'est choisi (« Système »). Le sélecteur de thème existant est inchangé.
- **Couleurs** : chaque jeton local prend la valeur d'un rôle de la charte v2.1, choisi par usage (correspondances dans `DESIGN.md`). Nouveaux jetons : `line-strong`, `button`, `button-hover`, `on-button`, `focus`, `warning-line`, `title-rule`, `picto-*`. Retirés : `relief`, `relief-active`, `dot`.
- **Boutons** : le principal est neutre (`button`), le secondaire en contour `line-strong`, les boutons à bascule pressés en `primary-soft` avec liseré `primary` ; plus aucun aplat bleu de bouton. Anneau de focus `focus`.
- **Fini l'ombre pleine et les pois** : les cartes sont bordées d'un trait, les volets flottants d'un halo doux.
- **Polices** : Sora 600 pour les titres (remplace l'ancienne police de titres, fichiers retirés), Atkinson Hyperlegible et JetBrains Mono mises à jour, licences OFL jointes.
- **Favicon et pictogramme** de la charte, filet or sous le titre des pages Atelier LLM, RAG, MCP, Sécurité et Modèles.
- **Tests** : `tests/test_web_tokens.py` réaligné (blocs sombre d'abord, contrastes 4,5:1 et 3:1 dans les deux thèmes, valeurs issues de la charte, pas d'aplat bleu de bouton, plus de relief, polices et icône).
- **Captures** : `docs/media/charte-v2/` (six pages, clair et sombre).

### Limites

- Le GIF du README (`docs/assets/harness-lab-demo.gif`) reste à l'ancienne charte : à refaire ; une capture fixe clair et sombre est ajoutée à côté. Son compositeur, `tools/demo/compose.py`, a déjà les couleurs v2.1 ; ses polices restent Segoe UI (outil Windows, repli documenté par la charte).
- L'Atelier Harnais n'a pas de titre visible (`h1` réservé aux lecteurs d'écran) : pas de filet or sur cette page.
- Les cinq fonds doux de discipline se réduisent à quatre teintes (harnais et neutre partagent `surface-alt`) : la discipline se lit par sa bordure et son libellé.
- Historique non migré : `docs/recette/`, `docs/assets/` (anciennes images), `tools/e2e/screenshots/`, `_bmad-output/` (le texte de `DESIGN.md` hors du renvoi à la charte parle encore de relief et de pois).
- Les repli de compatibilité de l'ancien nom du projet (variables d'environnement, dossier de données) restent dans `install.*`, `compat.py`, `config.py`, `tools/bench/v2s6_decision_bench.py`, `tests/test_compat.py` et `tests/test_installers.py`. Ce sont des mentions de provenance (renommage 2.0.0), pas de charte.
- `DESIGN.md` (`_bmad-output/`) est retouché : ses jetons de frontmatter sont la source que lisent `tests/test_web_tokens.py` et l'E2E (`_design_rgb`).


## 2.0.0 — 2026-11-03

Changement majeur : le projet WaveStack devient **HarnessLab**, une version publique générique.

- **Nouveau nom** : dépôt `harness-lab` (https://github.com/Aliquanto3/harness-lab), nom affiché
  HarnessLab, paquet Python `harness_lab` (ancien `wavestack`), commande `uv run harness-lab`
  (l'ancienne commande `wavestack` n'existe plus), configuration `harness-lab.toml` (ancien
  `wavestack.toml`).
- **Nouvelle charte** : palette générique (bleu pétrole, orange brûlé), mêmes noms de jetons,
  nouveau pictogramme et logotype texte, nouveau favicon. Nouveau jeton `on-status` : texte sur
  les aplats d'état (succès, erreur, accent), blanc en clair et encre en sombre.
- **Variables d'environnement** : préfixe `HARNESS_LAB_` (ancien `WAVESTACK_`). Les anciens noms
  restent lus en repli, avec un avertissement de dépréciation : `WAVESTACK_DATA_DIR` par
  l'application, les variables des installeurs (`WAVESTACK_INSTALL_DIR`, `WAVESTACK_MODELS`…) et
  `WAVESTACK_LLAMA_SERVER` du banc. Les variables internes des tests et des E2E
  (`HARNESS_LAB_TEST_*`, `HARNESS_LAB_E2E_*`) sont seulement renommées.
- **Dossier de données** : `%LOCALAPPDATA%\HarnessLab` sous Windows, `~/.local/share/harness-lab`
  ailleurs. Au premier lancement (ou à la première installation), l'ancien dossier
  (`%LOCALAPPDATA%\WaveStack`, `~/.local/share/wavestack`) est copié vers le nouveau si celui-ci
  n'existe pas encore ; l'ancien n'est jamais supprimé.
- **Anciens liens** : GitHub redirige `Aliquanto3/wavestack` vers `Aliquanto3/harness-lab`.
  Mettez à jour vos clones : `git remote set-url origin https://github.com/Aliquanto3/harness-lab.git`.
  Les réglages d'affichage gardés par le navigateur (thème, volets) repartent de leurs valeurs
  par défaut : leurs clés passent de `wavestack.*` à `harness_lab.*`.
