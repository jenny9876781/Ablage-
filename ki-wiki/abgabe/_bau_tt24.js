const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,AlignmentType,LevelFormat}=require('docx');
const HEAD='1F3A4D',ACC='2E6E8E';
const run=x=>typeof x==='string'?new TextRun(x):x;
const B=t=>new TextRun({text:t,bold:true});
const H=t=>new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun(t)]});
const L=t=>new Paragraph({numbering:{reference:'b',level:0},spacing:{after:50},children:(Array.isArray(t)?t:[t]).map(run)});
const LINE='______________________________________________';
const kids=[
 new Paragraph({spacing:{after:40},children:[new TextRun({text:'KOMDIS KI-SCHULUNG · THEORIETAG 24',bold:true,color:ACC,size:18,characterSpacing:30})]}),
 new Paragraph({spacing:{after:60},children:[new TextRun({text:'Meine Einschätzung zum Kurs',bold:true,size:36,color:HEAD})]}),
 new Paragraph({spacing:{after:160},children:[new TextRun({text:'Jennifer Preisigke · November 2026',size:18,color:'666666'})]}),
 H('Was mir am meisten gebracht hat'),
 L([B('Praxisprojekt mit echtem Prozess: '),'kein Beispielfall, sondern ein Ablauf aus meinem Betrieb – am Ende ein Dokument, das mein Chef entscheiden kann.']),
 L([B('Die Rechenfallen (TT20/TT23): '),'Ohne sie hätte ich mit dem Verrechnungssatz gerechnet und den Nutzen fast vervierfacht.']),
 L([B('Datenschutz und Recht (TT18): '),'Erst dadurch wurde klar, dass ein Schulungszugang kein Firmenzugang mit AVV ist – mein wichtigster Aha-Moment.']),
 L([B('KI-Wiki (TT21): '),'Wissen bleibt erhalten statt im Chat zu verschwinden; ich konnte über mehrere Tage am selben Stand weiterarbeiten.']),
 L([B('Gespräch mit dem Chef als Pflichtaufgabe: '),'hat die Richtung meines Projekts gedreht – von „schneller“ zu „genauer“.']),
 H('Was ich gelernt habe – über KI hinaus'),
 L('KI-Ergebnisse immer gegenprüfen: Die KI hat Schwachstellen vermutet, die längst gelöst waren.'),
 L('Kennzahlen gehören an den Vorgang, nicht an die Person.'),
 L('Ein ehrliches kleines Ergebnis überzeugt mehr als ein schönes großes.'),
 H('Tool-Bewertung'),
 L([B('Claude / Claude Code: '),'sehr stark für Auswertungen, Skills und Dokumente. Schwäche: Ergebnisse müssen genau geprüft werden – die Fehler im Skill zeigen das.']),
 L([B('Gamma, Voice Bots, Vision Board (TT19): '),LINE]),
 L([B('ChatGPT / weitere Tools aus dem Tool-Check: '),LINE]),
 H('Was ich mir anders gewünscht hätte'),
 L('Übungsergebnisse früherer Tage gingen verloren (z. B. mein Business Case aus TT20) – besser von Anfang an ein Wiki oder eine feste Ablage führen.'),
 L('Der Einstieg in Claude Code und Markdown-Wikis ist für Teilnehmende ohne Vorerfahrung steil.'),
 L('Ein klarer Hinweis gleich zu Kursbeginn: „Keine echten Firmendaten im Schulungszugang.“'),
 L([B('Tempo, Umfang, Theorie-Praxis-Verhältnis: '),LINE]),
 H('Mein Fazit in einem Satz'),
 new Paragraph({spacing:{before:60},children:[new TextRun({text:'„Ich gehe mit einem echten Projekt raus, das mein Chef entscheiden kann – und mit dem Bewusstsein, dass KI schnell ist, aber erst mit Kontrolle verlässlich wird.“',italics:true,size:22,color:HEAD})]}),
];
const doc=new Document({styles:{default:{document:{run:{font:'Arial',size:20}}},paragraphStyles:[{id:'Heading2',name:'Heading 2',basedOn:'Normal',next:'Normal',quickFormat:true,run:{font:'Arial',size:22,bold:true,color:ACC},paragraph:{spacing:{before:180,after:60},keepNext:true,outlineLevel:1}}]},
 numbering:{config:[{reference:'b',levels:[{level:0,format:LevelFormat.BULLET,text:'•',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:360,hanging:260}}}}]}]},
 sections:[{properties:{page:{margin:{top:1000,bottom:900,left:1134,right:1134}}},children:kids}]});
Packer.toBuffer(doc).then(b=>fs.writeFileSync(process.argv[2],b));
