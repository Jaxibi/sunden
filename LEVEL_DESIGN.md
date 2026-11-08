# Sunden — Niveau 1 : « La Crypte Gluante »

Forêt de Sunden (tutoriel) → Crypte d'Émeraude (1er donjon) → Le Roi Gluant (1er boss).
Durée visée : 12 à 18 minutes pour un premier passage.

---

## 1. Diagnostic du jeu existant

| Point | État actuel |
|---|---|
| Caméra & contrôles | Vue isométrique orthographique (≈ 11 × 6 m à l'écran), 320×180 agrandi. Déplacement 5 m/s, relatif à la caméra. |
| Verbes du joueur | Combo 3 coups (1 + 1 + 2 dégâts, le 3e tournoie à 360°), roulade invulnérable 0,26 s, visée automatique au contact. |
| Ressource limitante | PV (100). **Aucune source de soin** et aucune récompense : la seule boucle était une arène à vagues infinies. |
| Ennemis | Slime (3 PV, bond télégraphié) et squelette (5 PV, coup de taille télégraphié) : deux axes déjà orthogonaux (harceleur rapide / frappeur lourd). |
| Friction | Pas d'objectif, pas de répit, pas d'espace (arène carrée), pas d'usage tactique de la roulade autre que fuir. |

**Piliers retenus**
1. **Lisibilité du danger** — tout ce qui blesse s'annonce (télégraphe visuel + sonore) ; la mort est toujours « ma faute ».
2. **Rythme en dents de scie** — combat bref et intense, puis répit, butin et découverte.
3. **La roulade est une arme** — traverser le danger (piques, ondes du boss) plutôt que le fuir.

**Cohérence** : une crypte de pierre envahie par les slimes ; les squelettes sont les anciens gardiens,
le Roi Gluant a absorbé la couronne du roi enterré. Les jarres et caisses sont les offrandes de la crypte
(cœurs = provisions), les braseros sont les feux des veilleurs.

---

## 2. Boucles

| Échelle | Boucle |
|---|---|
| Micro (3–15 s) | Lire le télégraphe → rouler *dans* l'attaque ou hors portée → punir avec un combo complet (le 3e coup repousse et touche tout autour). |
| Core (1–3 min) | Entrer dans une salle → la herse se ferme → 2 vagues dont la composition change → la herse s'ouvre → jarres (soin) → brasero / découverte. |
| Méta (niveau) | Le donjon forme une **boucle** : le hall central, puis deux salles, un raccourci qui ramène au hall et ouvre la porte du boss. Le coffre caché donne les **Bottes de rafale** : la roulade blesse et repousse → elle change la façon de jouer, pas une stat. |

**Dilemme risque / récompense** : l'alcôve du coffre se trouve derrière un couloir de piques en vagues
et des jarres ; c'est facultatif, plus dangereux, mais l'objet transforme le combat de boss
(les mini-slimes se balaient en roulant).

---

## 3. Plan

```
            (haut de l'écran = nord-ouest)
 ┌──────────────┐          ┌───────────────────┐
 │  OSSUAIRE E4 ├─raccourci┤                   │
 │  (4) ⟂       │   ⇣      │   ARÈNE DU BOSS   │
 └──────┬───────┘   ⇣      │      Roi Gluant   ├─▶ Salle du trésor (fin)
        ⟂           ⇣      │                   │
 ┌──────┴───────┐ ┌─┴──────┴───┐  porte scellée │
 │ SALLE DES    ├⟂┤ HALL  E2 B2├──────▶──────────┘
 │ PIQUES  E3   │ │ (hub)      │
 └──────┬───────┘ └─────┬──────┘
        ┆ couloir piqué  ⟂
   ┌────┴───┐     ┌─────┴──────────┐
   │ALCÔVE C│     │ CLAIRIÈRE E1 B1│◀── passage piqué ◀── slime seul ◀── jarres ◀── DÉPART
   └────────┘     └────────────────┘                (bas de l'écran = sud-est)
   ⟂ herse   B brasero (checkpoint)   C coffre (Bottes de rafale)
```

Le niveau est décrit en ASCII dans `levels/niveau1.json` (généré par `tools/compose_level1.py`,
modifiable à la main) : une case = 1 m.

---

## 4. Progression *Kishōtenketsu*

| Acte | Lieu | Ce qui est appris / testé |
|---|---|---|
| **Ki** | Forêt | Bouger, frapper des jarres (aucun danger), un slime seul et lent à s'énerver, des piques qui montrent leur rythme. |
| **Shō** | Clairière (E1) + Hall (E2) | Combat en salle fermée. E2 introduit le squelette **seul** avant de le mêler aux slimes (harceleur + frappeur = deux axes d'attention). |
| **Ten** | Salle des piques (E3) | Les piques blessent **aussi les ennemis** : attirer les slimes sur les grilles. Le décor devient une arme. |
| **Ketsu** | Ossuaire (E4) | Examen du donjon : vagues mixtes échelonnées ; la victoire ouvre le raccourci et brise le sceau du boss. |
| Boss | Arène | Les trois actes en un seul combat (voir §6). |

---

## 5. Rythme

```
Intensité
  ^                                                         ┌ P3
  |                                              E4 ┐  ┌ P2 ┘│
  |                       E3 ┐            ┌──┐  ┌─┘  └──┘    │  Victoire
  |          E1 ┐   E2 ┐  ┌──┘└┐  alcôve  │  │  │  boss P1    │   ╲
  |  slime ┐ ┌──┘ ┌──┘  └┐ │   └────┐ ┌───┘  └──┘             └────▶
  |  ┌─────┘─┘ B1 ┘  B2   └─┘         └─┘   B2 (retour)
  +──────────────────────────────────────────────────────────────▶ temps
     forêt      clairière  hall   piques     ossuaire        boss
```

Après chaque salle : herse ouverte + jarres + 20 à 40 s sans menace (chemin, décor, brasero).

---

## 6. Le Roi Gluant (boss)

36 PV ≈ 9 combos. Le Roi est **vulnérable surtout après un écrasement** (étourdi), ce qui pousse
le joueur à lire, esquiver puis punir, plutôt qu'à rester collé au boss.

| Phase | PV | Comportement | Ce qui est testé |
|---|---|---|---|
| P1 | 36 → 24 | 2 petits bonds vers le héros, puis **écrasement** : ombre rouge au sol 0,9 s, impact (rayon 2 m, 20 dégâts), étourdi 1,4 s. | Lire le télégraphe, sortir de l'ombre, punir. |
| P2 | 24 → 12 | L'écrasement libère une **onde de choc** (anneau qui s'élargit jusqu'à 7 m) et 2 mini-slimes (4 max). | L'onde ne se fuit pas : il faut **rouler à travers** (invulnérable). Gérer les adds. |
| P3 | 12 → 0 | Rage : **3 écrasements enchaînés** (ombre 0,6 s), chacun avec onde ; puis long étourdissement 2,2 s. Plus d'adds. | Rythme de roulades, grosse fenêtre de punition. |

Transitions : rugissement (invulnérable 1,2 s), tremblement, les mini-slimes éclatent.

---

## 7. Chiffres

| Élément | Valeur | En coups / secondes |
|---|---|---|
| Héros | 100 PV, combo 1+1+2 | Combo complet ≈ 0,85 s |
| Slime | 3 PV | 3 coups (un combo) |
| Squelette | 5 PV | 4 coups (combo + 1) — l'ennemi « lourd » |
| Mini-slime (boss) | 2 PV | 2 coups |
| Roi Gluant | 36 PV | ≈ 9 combos, ≈ 60–90 s |
| Piques | 15 dégâts au héros, 1 aux ennemis | cycle 2,7 s : repos 1,6 / alerte 0,5 / sortie 0,4 / retrait 0,2 |
| Écrasement du boss | 20 (impact), 15 (onde) | |
| Cœur | +25 PV | jarre : 35 %, caisse : 60 % |
| Brasero | soin complet + point de retour | |
| Bottes de rafale | la roulade inflige 1 et repousse | |

Mort : retour au dernier brasero, PV pleins ; la salle en cours est réinitialisée, les salles finies le restent.
