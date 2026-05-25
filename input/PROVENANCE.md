# Hoststamp dictionary candidates

Committed review notes for the source lists used to build the Hoststamp
dictionary artifact. All sources below are compatible with redistribution in
this MIT-licensed project when their original license and attribution
requirements are preserved. Apache-2.0 / BSD-3-Clause / MIT sources need a
NOTICE-style attribution line; CC0 and factual data (star names, elements,
NATO) carry no obligation.

`clean%` = share of entries already DNS-label-safe as-is
(`^[a-z0-9-]+$` after lowercasing). Low values mean the list needs
ASCII-folding / space-and-punctuation stripping before use, not that
it is unusable — just more normalization work.

| List | Theme | License | N | Len | clean% (lower) | Sample |
| --- | --- | --- | --: | --- | --- | --- |
| `petname/adjectives.txt` | petname | Apache-2.0 | 449 | 2-8 | 100% | ready, chief, advanced, still, famous, equal |
| `petname/adverbs.txt` | petname | Apache-2.0 | 261 | 4-10 | 100% | willingly, awfully, inherently, slowly, lightly, terribly |
| `petname/names.txt` | petname (animals) | Apache-2.0 | 449 | 2-8 | 100% | hamster, ghost, mackerel, gar, wildcat, marten |
| `docker-moby/adjectives.txt` | docker/moby | Apache-2.0 | 108 | 3-13 | 100% | blissful, angry, sad, elated, upbeat, focused |
| `docker-moby/surnames.txt` | docker/moby (scientists) | Apache-2.0 | 245 | 2-89 | 97% | noyce, wozniak, newton, mirzakhani, benz, mcclintock |
| `haikunator/adjectives.txt` | haikunator | BSD-3-Clause | 91 | 3-9 | 100% | wispy, morning, bold, green, bitter, misty |
| `haikunator/nouns.txt` | haikunator | BSD-3-Clause | 95 | 3-10 | 100% | sky, shadow, glade, snowflake, night, mountain |
| `iau-star-names/star-names.txt` | IAU star names | factual / public domain | 443 | 1-15 | 99% | Hunahpu, Homam, Nusakan, Mago, Mira, Chechia |
| `corpora/greek-gods.txt` | Greek gods | CC0 | 31 | 3-10 | 100% | Hera, Zeus, Demeter, Aether, Aphrodite, Phanes |
| `corpora/greek-titans.txt` | Greek titans | CC0 | 33 | 3-10 | 100% | Coeus, Eos, Aura, Styx, Hyperion, Themis |
| `corpora/greek-monsters.txt` | Greek monsters | CC0 | 24 | 5-17 | 91% | Minotaur, Ophitaurus, Empousai, Hippalectryon, Mormo, Hydra |
| `corpora/roman-deities.txt` | Roman deities | CC0 | 25 | 3-12 | 96% | Mars, Apollo, Sol Invictus, Saturn, Janus, Veritas |
| `corpora/norse-gods.txt` | Norse gods | CC0 | 66 | 2-11 | 59% | Ēostre, Saxnōt, Þrúðr, Óðr, Sandraudiga, Fulla |
| `corpora/egyptian-gods.txt` | Egyptian gods | CC0 | 178 | 3-15 | 94% | brewing, star, snake, Thebes, love, cobra |
| `corpora/elements.txt` | Periodic elements | CC0 | 118 | 3-13 | 100% | Aluminum, Nitrogen, Polonium, Ytterbium, Hassium, Helium |
| `corpora/planets.txt` | Planets | CC0 | 13 | 4-8 | 100% | Mercury, Saturn, Ceres, Uranus, Haumea, Makemake |
| `corpora/minor-planets.txt` | Minor planets | CC0 | 1000 | 5-18 | 0% | 223 Rosa, 992 Swasey, 60 Echo, 594 Mireille, 754 Malabar, 556 Phyllis |
| `corpora/gemstones.txt` | Gemstones | CC0 | 350 | 3-24 | 92% | azurite, clinozoisite, atacamite, synthetic opal, astrophyllite, zeolite |
| `corpora/decorative-stones.txt` | Decorative stones | CC0 | 94 | 4-35 | 46% | frosterley marble, dunhouse blue, strzelin, verde antico, heavitree stone, flaggy limestone |
| `corpora/metals.txt` | Metals | CC0 | 92 | 3-13 | 100% | cadmium, indium, nickel, lead, einsteinium, praseodymium |
| `corpora/rivers.txt` | Rivers | CC0 | 217 | 2-22 | 81% | Niger, Jialing River, Sutlej, Rocha, Paraguay, Upper Ob |
| `corpora/winds.txt` | Winds | CC0 | 111 | 3-20 | 79% | puelche, levanter, washoe zephyr, furious fifties, autan, abrolhos |
| `corpora/oceans.txt` | Oceans/seas | CC0 | 146 | 6-23 | 3% | Somov Sea, Marmara Sea, Chukchi Sea, Baltic Sea, Norwegian Sea, Scotia Sea |
| `corpora/scientists.txt` | Scientists | CC0 | 328 | 5-38 | 3% | Elizabeth Blackwell, Ernest Rutherford, Lucretius, Albrecht von Haller, Ernesto Illy, Jane Marcet |
| `corpora/tolkien.txt` | Tolkien characters | CC0 | 595 | 3-27 | 51% | Elladan, Amlaith, Eärendil, Manthor, Haldir (First Age), Galador |
| `corpora/neutral-names.txt` | Neutral given names | CC0 | 664 | 2-12 | 95% | Tony, Oakley, Lumo, Lake, October, Turhan |
| `facts/nato-phonetic.txt` | NATO phonetic | public domain | 26 | 4-8 | 100% | Victor, Kilo, Tango, Yankee, Zulu, Delta |

## Full samples (20 random per list)

### petname — `petname/adjectives.txt` (449, len 2-8, Apache-2.0, src: github.com/dustinkirkland/golang-petname (petname.go))

ready, chief, advanced, still, famous, equal, eminent, composed, steady, certain, sacred, obliging, calm, powerful, joint, allowing, allowed, careful, electric, engaging

### petname — `petname/adverbs.txt` (261, len 4-10, Apache-2.0, src: github.com/dustinkirkland/golang-petname (petname.go))

willingly, awfully, inherently, slowly, lightly, terribly, newly, actively, happily, socially, promptly, greatly, lately, privately, evenly, endlessly, rightly, entirely, rarely, publicly

### petname (animals) — `petname/names.txt` (449, len 2-8, Apache-2.0, src: github.com/dustinkirkland/golang-petname (petname.go))

hamster, ghost, mackerel, gar, wildcat, marten, weevil, foal, bedbug, yak, caribou, llama, pipefish, macaque, lamprey, stingray, wahoo, garfish, stag, spaniel

### docker/moby — `docker-moby/adjectives.txt` (108, len 3-13, Apache-2.0, src: github.com/moby/moby@v24.0.7 pkg/namesgenerator)

blissful, angry, sad, elated, upbeat, focused, boring, busy, heuristic, festive, kind, relaxed, zealous, happy, cranky, hardcore, great, eager, serene, fervent

### docker/moby (scientists) — `docker-moby/surnames.txt` (245, len 2-89, Apache-2.0, src: github.com/moby/moby@v24.0.7 pkg/namesgenerator)

noyce, wozniak, newton, mirzakhani, benz, mcclintock, meninsky, chaplygin, kowalevski, pike, dirac, cerf, jemison, haibt, elgamal, williamson, merkle, nobel, lederberg, davinci

### haikunator — `haikunator/adjectives.txt` (91, len 3-9, BSD-3-Clause, src: github.com/Atrox/haikunatorgo (haikunator.go))

wispy, morning, bold, green, bitter, misty, polished, late, broad, frosty, square, weathered, shrill, plain, wandering, restless, delicate, jolly, dawn, holy

### haikunator — `haikunator/nouns.txt` (95, len 3-10, BSD-3-Clause, src: github.com/Atrox/haikunatorgo (haikunator.go))

sky, shadow, glade, snowflake, night, mountain, math, flower, credit, salad, rice, bush, boat, cell, dawn, term, dew, violet, star, bread

### IAU star names — `iau-star-names/star-names.txt` (443, len 1-15, factual / public domain, src: IAU WGSN Catalog of Star Names (IAU-CSN), pas.rochester.edu/~emamajek/WGSN)

Hunahpu, Homam, Nusakan, Mago, Mira, Chechia, Mouhoun, Zubenelgenubi, Acrab, Sabik, Shama, Alshat, Saclateni, Mirzam, Suhail, Cursa, Tania, Praecipua, Fuyue, Alshain

### Greek gods — `corpora/greek-gods.txt` (31, len 3-10, CC0, src: dariusk/corpora)

Hera, Zeus, Demeter, Aether, Aphrodite, Phanes, Tartarus, Hephaestus, Chaos, Hemera, Gaia, Artemis, Nemesis, Hypnos, Dionysus, Athena, Uranus, Poseidon, Ares, Pontus

### Greek titans — `corpora/greek-titans.txt` (33, len 3-10, CC0, src: dariusk/corpora)

Coeus, Eos, Aura, Styx, Hyperion, Themis, Menoeltius, Leto, Tethys, Phoebe, Crius, Eurynome, Helios, Cronus, Selene, Perses, Prometheus, Iapetus, Clymene, Theia

### Greek monsters — `corpora/greek-monsters.txt` (24, len 5-17, CC0, src: dariusk/corpora)

Minotaur, Ophitaurus, Empousai, Hippalectryon, Mormo, Hydra, Gorgon, Telekhines, Hippocampus, Synthian Dracanus, Icthyocentaur, Satyr, Taraxippus, Harpy, Siren, Lamia, Caucasian Eagle, Typhon, Manticore, Arachne

### Roman deities — `corpora/roman-deities.txt` (25, len 3-12, CC0, src: dariusk/corpora)

Mars, Apollo, Sol Invictus, Saturn, Janus, Veritas, Terra, Vesta, Caelus, Bacchus, Ceres, Pluto, Venus, Diana, Neptune, Juno, Nox, Cupid, Mercury, Jupiter

### Norse gods — `corpora/norse-gods.txt` (66, len 2-11, CC0, src: dariusk/corpora)

Ēostre, Saxnōt, Þrúðr, Óðr, Sandraudiga, Fulla, Sif, Eir, Meili, Hermóðr, Snotra, Irpa, Zisa, Vili, Sinthgunt, Syn, Frigg, Njörun, Forseti, Lofn

### Egyptian gods — `corpora/egyptian-gods.txt` (178, len 3-15, CC0, src: dariusk/corpora)

brewing, star, snake, Thebes, love, cobra, bull, child, home, women, crown, order, sky, scarab beetle, childbirth, healing, perfume, hunting, justice, stars

### Periodic elements — `corpora/elements.txt` (118, len 3-13, CC0, src: dariusk/corpora)

Aluminum, Nitrogen, Polonium, Ytterbium, Hassium, Helium, Magnesium, Berkelium, Meitnerium, Gallium, Titanium, Iodine, Europium, Samarium, Nickel, Roentgenium, Tellurium, Livermorium, Oxygen, Indium

### Planets — `corpora/planets.txt` (13, len 4-8, CC0, src: dariusk/corpora)

Mercury, Saturn, Ceres, Uranus, Haumea, Makemake, Jupiter, Pluto, Neptune, Mars, Eris, Earth, Venus

### Minor planets — `corpora/minor-planets.txt` (1000, len 5-18, CC0, src: dariusk/corpora)

223 Rosa, 992 Swasey, 60 Echo, 594 Mireille, 754 Malabar, 556 Phyllis, 63 Ausonia, 766 Moguntia, 322 Phaeo, 59 Elpis, 52 Europa, 599 Luisa, 489 Comacina, 515 Athalia, 942 Romilda, 874 Rotraut, 544 Jetta, 162 Laurentia, 984 Gretia, 521 Brixia

### Gemstones — `corpora/gemstones.txt` (350, len 3-24, CC0, src: dariusk/corpora)

azurite, clinozoisite, atacamite, synthetic opal, astrophyllite, zeolite, elaeolite, muscovite, bronzite, stishovite, erythrite, susannite, andesine, tinaksite, obsidian, vesuvianite, synthetic alexandrite, stichtite, scheelite, ivory

### Decorative stones — `corpora/decorative-stones.txt` (94, len 4-35, CC0, src: dariusk/corpora)

frosterley marble, dunhouse blue, strzelin, verde antico, heavitree stone, flaggy limestone, marmara, comblanchien, steatite, hall dale, pierre d'euville, burdur beige marble, ancaster stone, skała, portoro buono, chalk, portland independent bottom whitbed, dunhouse buff, portland bowers saunders whitbed, kośmin

### Metals — `corpora/metals.txt` (92, len 3-13, CC0, src: dariusk/corpora)

cadmium, indium, nickel, lead, einsteinium, praseodymium, silver, zinc, lutetium, tin, ununpentium, scandium, aluminium, ununtrium, sodium, ununquadium, chromium, darmstadtium, iron, cobalt

### Rivers — `corpora/rivers.txt` (217, len 2-22, CC0, src: dariusk/corpora)

Niger, Jialing River, Sutlej, Rocha, Paraguay, Upper Ob, Krishna, Rio Grande, Madre de Dios, Zhu Jiang, Saint Louis, Milk, Vltava, Nelson, Little Yenisei, Han, Amu Darya, Tagus, Ob, Mackenzie

### Winds — `corpora/winds.txt` (111, len 3-20, CC0, src: dariusk/corpora)

puelche, levanter, washoe zephyr, furious fifties, autan, abrolhos, halny, suêtes, buran, föhn, cers, southerly buster, libeccio, nigeq, sharqi, norte, alisio, brickfielder, bayamo, shamal

### Oceans/seas — `corpora/oceans.txt` (146, len 6-23, CC0, src: dariusk/corpora)

Somov Sea, Marmara Sea, Chukchi Sea, Baltic Sea, Norwegian Sea, Scotia Sea, Balearic Sea, King Haakon VII Sea, East Siberian Sea, Salish Sea, Salton Sea, Caspian Sea, Banda Sea, Sea of Chiloé, Cosmonauts Sea, Aral Sea, Sea of Azov, Aegean Sea, Spencer Gulf, Celebes Sea

### Scientists — `corpora/scientists.txt` (328, len 5-38, CC0, src: dariusk/corpora)

Elizabeth Blackwell, Ernest Rutherford, Lucretius, Albrecht von Haller, Ernesto Illy, Jane Marcet, Louis Pasteur, Grace Murray Hopper, Hedy Lamarr, Edwin Herbert Land, Carl Bosch, Keisuke Ito, Alexander Von Humboldt, Nicolaus Copernicus, Galen, Francis Bacon, Muhammad ibn Musa al-Khwarizmi, John Dalton, Ivan Pavlov, Georg Ohm

### Tolkien characters — `corpora/tolkien.txt` (595, len 3-27, CC0, src: dariusk/corpora)

Elladan, Amlaith, Eärendil, Manthor, Haldir (First Age), Galador, Argeleb I, Ilúvatar, Tar Telemnar, Manwë, Tinúviel, Hallas, Amrothos, Bergil, Fingolfin, Dior, Yávien, Finwë, Angrod, Beorn

### Neutral given names — `corpora/neutral-names.txt` (664, len 2-12, CC0, src: dariusk/corpora)

Tony, Oakley, Lumo, Lake, October, Turhan, Rylan, Dana, Mika, Sydney, Gili, Jade, Arya, Adair, Sani, Sharon, Gwynn, Marlee, North, Blair

### NATO phonetic — `facts/nato-phonetic.txt` (26, len 4-8, public domain, src: ICAO/NATO alphabet (fact))

Victor, Kilo, Tango, Yankee, Zulu, Delta, Juliett, Quebec, Xray, November, Whiskey, Golf, Lima, Echo, India, Charlie, Uniform, Oscar, Sierra, Foxtrot
