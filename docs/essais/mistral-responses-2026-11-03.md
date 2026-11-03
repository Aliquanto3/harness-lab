# Essai : l'API Responses de Mistral avec l'adaptateur `openai_responses` (2026-11-03)

> **Suite** : correctif appliqué dans la PR #172 (version 1.7.4). L'adaptateur affiche et
> renvoie le raisonnement en clair, et `wavestack.toml` porte l'exemple commenté
> `mistral_responses`. Les constats ci-dessous décrivent l'adaptateur avant ce correctif.

Test rapide, pas une story. Script jetable, resté sur la branche `test/mistral-responses` :
`tools/essais/mistral_responses.py` (lit la clé par
`config.cloud_key`, entrée `mistral`, et masque toute sortie par `engine.mask`). Corps écrit par
le traducteur `openai_responses` de `context/render.py`, flux lu par `OpenAIResponsesEngine`,
sans modification de l'un ni de l'autre.

Modèle : `mistral-large-4` (le compte y a accès ; `magistral-*` et `mistral-small-latest` aussi
listés). Scénario : prompt système de ~2 400 tokens, un outil `get_time`, tour 1 (appel
d'outil), tour 2 (résultat de l'outil, réponse finale), tour 2 bis (items reasoning renvoyés).
17 appels au total, environ 42 000 tokens d'entrée (dont ~90 % lus dans le cache) et 1 000 de
sortie : environ 0,02 $ si le prix de Large 4 est proche de celui de Large 3 (0,50 $ / 1,50 $
par million, non relevé pour Large 4, à vérifier sur mistral.ai/pricing).

## Ce qui marche

| Point | Résultat |
|---|---|
| `store: false` | accepté (200), sans effet visible : l'API est sans état. |
| `include: ["reasoning.encrypted_content"]` | accepté (200), ignoré : `encrypted_content` revient à `null`. |
| `reasoning.summary: "auto"` | accepté, ignoré : `summary` revient vide. |
| `instructions`, `input`, `tools` (`strict: false`), `max_output_tokens` | acceptés. |
| Streaming SSE | `response.created`, `in_progress`, `output_item.added/done`, `content_part.*`, `output_text.delta`, `function_call_arguments.delta/done`, `response.completed` : mêmes noms qu'OpenAI, lus par l'adaptateur. |
| Appels d'outil | `function_call` lu (`call_id`, nom, arguments en flux) ; `function_call_output` accepté au tour 2, réponse finale correcte. |
| `usage` | `input_tokens`, `output_tokens`, `output_tokens_details.reasoning_tokens`, `input_tokens_details.cached_tokens` (2 304 sur 2 397 dès le 2e appel) : le pivot de l'adaptateur les reprend tels quels. La story « cache visible » peut s'appuyer dessus. Mistral ajoute `input_tokens_details.cache_write_tokens` (0 ici), que le pivot ignore. |
| Item reasoning renvoyé en clair | accepté (200) au tour 2 bis, tel que reçu (`content` en clair, `encrypted_content: null`, `summary: []`, `status`), +41 tokens d'entrée. |

Aucune erreur 422 dans tout l'essai.

## Ce qui casse

1. **Le raisonnement n'est pas affiché.** Mistral diffuse son raisonnement en clair par
   `response.reasoning_text.delta` (`item_id`, `output_index`, `content_index`, `delta`),
   et non par `response.reasoning_summary_text.delta`, seul événement que lit l'adaptateur.
   Le canal Raisonnement reste vide, alors que le modèle raisonne (34 à 58 tokens par tour).
2. **Les items reasoning ne sont pas gardés.** `_reasoning_items` ne garde qu'un item qui a un
   `encrypted_content` ; ceux de Mistral n'en ont pas (le texte est dans `content`). Ils ne
   repartent donc jamais. Le tour 2 marche sans eux (pas de boucle d'outil observée), mais la
   brique Raisonnement ne montre pas le renvoi, et le journal brut (`raw_output`) les garde.
3. **`effort: "none"` refusé (400, pas 422)** sur `mistral-large-4` :
   « reasoning_effort none is not supported for this model, supported values: high, low,
   medium ». Sans champ `reasoning`, le modèle raisonne quand même. Il ne s'éteint donc pas.

## Changement minimal proposé (appliqué dans la PR #172, avec l'attribution du texte en clair à la brique Raisonnement)

Adaptateur `src/wavestack/models/openai_responses.py`, deux retouches :

- lire `response.reasoning_text.delta` comme `response.reasoning_summary_text.delta` (canal
  `reasoning`, masqué, parties séparées par `\n\n` selon `(item_id, content_index)`) ;
- dans `_reasoning_items`, garder aussi un item sans `encrypted_content` qui a un `content`
  non vide (raisonnement en clair). Un item OpenAI ne change pas de traitement.

Tests : deux cas dans `tests/test_openai_responses.py` sur le faux serveur SSE (flux
`reasoning_text.delta` affiché ; item en clair renvoyé au tour suivant).

Préréglage (exemple à recopier dans `settings.json`, ou entrée `mistral_responses` désactivée
par défaut dans `wavestack.toml`) :

```toml
[[cloud.models]]
id = "mistral_responses"
provider = "Mistral AI"
base_url = "https://api.mistral.ai/v1"
model = "mistral-large-4"
api = "openai_responses"
max_tokens_field = "max_output_tokens"
tools = true
context = 131072          # à vérifier sur la fiche de Large 4
training = "opt_out"
key_env = "MISTRAL_API_KEY"
min_interval_s = 1
# pricing et impacts : à relever (prix de Large 4, nom du modèle dans EcoLogits)

[cloud.models.reasoning]
format = "reasoning_items"
always = true             # effort « none » refusé (400) : il raisonne toujours
on = { reasoning = { effort = "low" } }
resend = true
```

Aucune option à désactiver par fournisseur : `store` et `include` passent tels quels.
La clé : l'entrée `mistral_responses` a un autre id que `mistral`, donc une clé à saisir
une fois au diagnostic (ou `MISTRAL_API_KEY`), sur le même hôte.

## Ligne pour `veille-agents-code/tests-pratiques/PLAN.md`

```
| Mistral Responses dans wavestack | fait le 2026-11-03 (`wavestack`, `docs/essais/mistral-responses-2026-11-03.md`, PR #172, v1.7.4) | OK après correctif : aucun 422 avec `mistral-large-4` (`store` et `include` acceptés et ignorés), streaming, appels d'outil, `usage` et `cached_tokens` OK ; le raisonnement en clair de Mistral (`response.reasoning_text.delta`, items `content` sans `encrypted_content`) est maintenant affiché et renvoyé par l'adaptateur ; `effort: "none"` refusé (400), d'où un exemple de préréglage `mistral_responses` avec `always = true`. Essai ~0,02 $. |
```
