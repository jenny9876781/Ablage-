const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,WidthType,ShadingType,HeadingLevel,AlignmentType,LevelFormat,PageBreak,Footer,PageNumber,BorderStyle,VerticalAlign,ImageRun}=require('docx');
const IMG=(f,w,h)=>new Paragraph({spacing:{after:120},children:[new ImageRun({type:'png',data:fs.readFileSync(f),transformation:{width:w,height:h},altText:{title:f,description:f,name:f}})]});
const W=9638, HEAD='1F3A4D', ACC='2E6E8E', RED='F4CCCC',YEL='FFF2CC',GRN='D9EAD3',GREY='EEF3F6';
const run=x=>typeof x==='string'?new TextRun(x):x;
const P=(t,o={})=>new Paragraph({spacing:{after:120,line:276},...o,children:(Array.isArray(t)?t:[t]).map(run)});
const B=t=>new TextRun({text:t,bold:true});
const I=t=>new TextRun({text:t,italics:true});
const H1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun(t)]});
const H2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun(t)]});
const L=t=>new Paragraph({numbering:{reference:'b',level:0},spacing:{after:70,line:264},children:(Array.isArray(t)?t:[t]).map(run)});
const N=t=>new Paragraph({numbering:{reference:'n',level:0},spacing:{after:70},children:(Array.isArray(t)?t:[t]).map(run)});
const BR=()=>new Paragraph({children:[new PageBreak()]});
const SP=()=>new Paragraph({spacing:{after:60},children:[]});
function T(widths,rows,shade,opt={}){
  const tot=widths.reduce((a,b)=>a+b,0); const ws=widths.map(w=>Math.round(w/tot*W)); ws[ws.length-1]+=W-ws.reduce((a,b)=>a+b,0);
  return new Table({width:{size:W,type:WidthType.DXA},columnWidths:ws,rows:rows.map((r,i)=>new TableRow({tableHeader:i===0&&!opt.nohead,cantSplit:true,children:r.map((c,j)=>{
    const head=i===0&&!opt.nohead; let fill=head?HEAD:(shade?shade(i,j,String(c)):null);
    const bold=head||(opt.boldRows&&opt.boldRows.includes(i))||(opt.boldCol0&&j===0);
    return new TableCell({width:{size:ws[j],type:WidthType.DXA},margins:{top:70,bottom:70,left:100,right:100},verticalAlign:VerticalAlign.CENTER,
      shading:fill?{type:ShadingType.CLEAR,color:'auto',fill}:undefined,
      children:[new Paragraph({alignment:(opt.right&&opt.right.includes(j)&&!head)?AlignmentType.RIGHT:AlignmentType.LEFT,children:[new TextRun({text:String(c),bold,color:head?'FFFFFF':undefined,size:18})]})]});})}))});
}
const amp=c=>/^Rot/.test(c)?RED:/^Gelb/.test(c)?YEL:/^Grün/.test(c)?GRN:null;
const box=(title,lines,fill=GREY)=>new Table({width:{size:W,type:WidthType.DXA},columnWidths:[W],rows:[new TableRow({children:[new TableCell({width:{size:W,type:WidthType.DXA},margins:{top:140,bottom:140,left:200,right:200},shading:{type:ShadingType.CLEAR,color:'auto',fill},
  borders:{left:{style:BorderStyle.SINGLE,size:24,color:ACC},top:{style:BorderStyle.NONE,size:0,color:'FFFFFF'},bottom:{style:BorderStyle.NONE,size:0,color:'FFFFFF'},right:{style:BorderStyle.NONE,size:0,color:'FFFFFF'}},
  children:[new Paragraph({spacing:{after:80},children:[new TextRun({text:title,bold:true,color:HEAD,size:22})]}),...lines.map(l=>new Paragraph({spacing:{after:60},children:(Array.isArray(l)?l:[l]).map(run)}))]})]})]});

// Swimlane: rows = roles, cols = steps 1..9
const sw=[['','1','2','3','4','5','6','7','8','9'],
 ['GF / Berater','Termin ⚠S1','Fahrt','','','','','','Freigabe ⚠S5c',''],
 ['Assistenz','','','Export','Bericht (Skill) ⚠S5a','Prüfen ⚠S5b','Nachtrag ⚠S1','Pflege','','Versand'],
 ['Partnerfirma','','','','','','','','','erhält']];
const swShade=(i,j,c)=>c.includes('⚠')?RED:(c&&j>0?'DCEAF2':(j===0?GREY:null));

const kids=[
 // Deckblatt
 new Paragraph({spacing:{before:2400,after:120},children:[new TextRun({text:'PRAXISPROJEKT KI-SCHULUNG',bold:true,color:ACC,size:22,characterSpacing:40})]}),
 new Paragraph({spacing:{after:200},children:[new TextRun({text:'Vom schnellen zum verlässlichen Monatsbericht',bold:true,size:52,color:HEAD})]}),
 P([new TextRun({text:'KI im monatlichen Projekt-Zeit- und Kostenbericht einer Beratungsfirma',size:28,color:'444444'})],{spacing:{after:1600}}),
 P([new TextRun({text:'Jennifer Preisigke',bold:true,size:22})],{spacing:{after:40}}),
 P([new TextRun({text:'Komdis KI-Schulung · Abschlussdokument · Abgabe Theorietag 24 · November 2026',size:20,color:'555555'})]),
 P([new TextRun({text:'Hinweis: Firmen-, Projekt- und Personennamen sind neutralisiert (Rollen statt Namen). Gehälter sind nur als Größenordnung (interner Stundensatz) enthalten.',italics:true,size:16,color:'777777'})],{spacing:{before:1200}}),
 BR(),

 // Management-Seite
 H1('Auf einen Blick'),
 box('Das Problem',[ 'Jeden Monat werden Kalendertermine und Fahrten zu Kosten je Projekt zusammengeführt. Von Hand dauerte das 12–16 Stunden. Seit Juli 2026 erledigt ein Claude-Skill das in etwa einer Stunde, plus ca. einer Stunde erneuter Prüfung. Damit ist das Tempo-Problem gelöst, aber ein neues ist entstanden: Die Geschäftsführung ist nicht sicher, ob der Bericht stimmt. Zwischen Versionen weichen Vormonate ab, Zuordnungen waren teils falsch, und der Bericht ist unübersichtlich.']),
 SP(),
 IMG('vorher_nachher.png',620,160),
 T([3,3,3],[['Zeit je Bericht','Ergebnis pro Jahr','Lohnt sich ab'],['früher 12–16 h · heute ca. 2 h','Jahr 1: +2.005 € · ab Jahr 2: +3.174 €','5,9 h Ersparnis pro Monat (heute: 10 h)']],(i)=>i===1?'DCEAF2':null,{boldRows:[1]}),
 SP(),
 box('Empfehlung: Ja – als Pilot über drei Monatsberichte',[[B('1. '),'Einen Claude-Team-Account für die Firma einrichten: Geschäftstarif mit Auftragsverarbeitungsvertrag (AVV). Bis dahin werden keine echten Firmendaten verarbeitet (Sofortmaßnahme).'],[B('2. '),'Den Skill im Dezember mit Claude Code prüfen und absichern: feste Versionsregel, Prüfblatt für die Vormonate, Begründung je Zuordnung.'],[B('3. '),'Die Auswertung „Auslastung je Mitarbeiter“ entfernen. Damit bleibt der Einsatz im minimalen Risiko der KI-Verordnung.']],'E8F1E4'),
 SP(),
 box('Nächster Schritt',['Entscheidung der Geschäftsführung über den Team-Account bis 30.11.2026. Danach startet der Pilot mit dem Novemberbericht. In zwölf Monaten läuft der Bericht im Regelbetrieb, auch in der Vertretung.']),
 BR(),

 // B1
 H1('1  Prozess & Ist-Zustand'),
 H2('1.1 Prozess-Kandidaten im Härtetest'),
 P('Geprüft nach der Faustregel aus dem Kurs: 5–15 Schritte, mehrere Beteiligte, wiederkehrend, eine Zahl dazu. Dazu kommen ein echter Schmerzpunkt und die Frage, ob eine Verbesserung der Chefin oder dem Chef auffallen würde.'),
 T([2.2,2.1,1.9,1.7,1.9],[
  ['Kriterium','A Projekt-Zeit-/Kostenbericht','B Zeiterfassung Team','C M&A-Angebot','D Inventarauflösung'],
  ['5–15 Schritte','✔ 9','✔ 7','✔ ca. 8','~ über 15'],
  ['Mehrere Beteiligte','✔ GF, Berater, Assistenz, Partnerfirma','✔ 3 Mitarbeitende, Assistenz, Vorgesetzte','~ GF, Assistenz','✔'],
  ['Wiederkehrend','✔ monatlich','✔ monatlich/Quartal','✘ je Deal, selten','✘ einmalig'],
  ['Zahl','✔ Stunden je Bericht','✔ Stunden je Monat','~','✔'],
  ['Schmerz','✔ Vertrauen in die Zahlen','~ fehlende Stempelungen','✔ Zeitdruck','✔ aber bald vorbei'],
  ['Sichtbar für Chef','✔ Abrechnung, Steuerung','~','✔','✘ anderes Unternehmen'],
  ['Daten grob','Gelb','Rot (Krankheitsdaten)','Rot (vertrauliche Deal-Zahlen)','Gelb'],
  ['Häkchen','6 / 6','4 / 6','3 / 6','3 / 6']],(i,j)=>j===1?GRN:null,{boldCol0:true}),
 H2('1.2 Entscheidung'),
 P(['Gewählt ist der ',B('monatliche Projekt-Zeit- und Kostenbericht'),'. Er hat als einziger Kandidat alle Kriterien erfüllt: Er läuft jeden Monat, betrifft vier Rollen, und die Geschäftsführung nutzt das Ergebnis direkt für Abrechnung und Projektsteuerung. Die Zeiterfassung habe ich verworfen, weil Krankheitstage Gesundheitsdaten sind und der KI-Hebel klein ist. Das M&A-Angebot kommt zu selten vor, und die Inventarauflösung ist ein einmaliges Projekt in einem anderen Unternehmen.']),
 P(['Besonderheit: Ein Teil des Prozesses läuft seit Juli 2026 bereits mit einem selbst gebauten Claude-Skill. Dadurch lässt sich ',B('vorher und nachher'),' vergleichen, und die nächste Stufe der Verbesserung wird sichtbar.']),
 P([B('Warum KI und nicht nur Excel? '),'Formeln, Power Query oder Makros können sauber strukturierte Daten zusammenrechnen. Die Kalendereinträge sind aber freier Text: Projektnamen, Kurzformen und Aufgaben stehen uneinheitlich im Betreff und müssen erkannt und Kategorien zugeordnet werden. Genau das kann die KI, Excel allein nur mit großem Pflegeaufwand.']),
 H2('1.3 Ist-Kette als Swimlane'),
 IMG('swimlane.png',640,232),
 SP(),
 T([0.5,3.2,1.5,1.7,3.2],[
  ['#','Schritt','Rolle','Werkzeug','Status heute'],
  ['1','Termin mit Projektname im Betreff eintragen','GF, Berater','Outlook','S4: fehlende Termine trägt die Assistenz händisch nach · Kurzformen gelöst'],
  ['2','Fahrt wird aufgezeichnet (praktisch nur GF)','GF','Fahrtenbuch-App','gelöst: feste Zuordnung Fahrzeug → Fahrer im Skill'],
  ['3','Monatsende: Kalender und Fahrten exportieren','Assistenz','Outlook, App','–'],
  ['4','Bericht erzeugen (Fahrt ↔ Termin, Kosten je Zeile)','Assistenz','Claude-Skill → Excel','S1: ältere gespeicherte Excel statt zuletzt bearbeiteter als Vorlage → Vormonate weichen ab'],
  ['5','Unklare Fälle prüfen','Assistenz','Excel','S2: falsche Zuordnungen, erst bei erneuter Prüfung entdeckt · Rückfragen nur noch ca. 15 Min.'],
  ['6','Fehlende Zeiten und Zusatzkosten nachtragen','Assistenz','Excel','S4 (siehe Schritt 1)'],
  ['7','Zuordnungstabellen pflegen','Assistenz','Excel','–'],
  ['8','Durchsicht und Freigabe','GF','Excel / Mail','S3: unübersichtlich, GF unsicher, ob es stimmt · Freigabe nur 15 Min.'],
  ['9','Versand an Partnerfirma / Abrechnung','Assistenz','Mail','meist bis zum 5. des Folgemonats']],(i,j,c)=>j===4&&/S\d/.test(c)?RED:(j===4&&/gelöst/.test(c)?GRN:null)),
 H2('1.4 Was die KI schon gelöst hat – und was nicht'),
 L([B('Gelöst durch den Skill: '),'Rechenzeit (von 12–16 h auf ca. 2 h), falsche Fahrerzuordnung, uneinheitliche Projektkurzformen, lange Rückfrage-Schleifen, Freigabe-Stau.']),
 L([B('Noch offen – das Tempo stimmt, die Genauigkeit noch nicht:'),'']),
 N([B('S1 Falsche Vorlage: '),'Der Skill hat eine ältere gespeicherte Excel statt der zuletzt bearbeiteten fortgeführt. Vormonate weichen dadurch ab.']),
 N([B('S2 Falsche Zuordnungen: '),'Einzelne Termine oder Fahrten landeten beim falschen Projekt und fielen erst bei erneuter Prüfung auf.']),
 N([B('S3 Unübersichtlich: '),'Der Bericht hat viele Reiter. Die GF kann bei der Freigabe nicht schnell erkennen, ob er stimmt.']),
 N([B('S4 Fehlende Termine: '),'Termine, die nicht im Kalender stehen, trägt die Assistenz von Hand nach.']),
 L([B('Aus dem Gespräch mit der Geschäftsführung (04.11.2026): '),'„Der Bericht ist zu unübersichtlich, und man ist sich nicht sicher, ob er stimmt.“ Gewünscht ist: ',B('genauer'),', nicht schneller.']),
 H2('1.5 Zahl zum Prozess'),
 L('12 Monatsberichte im Jahr, dazu Jahresauswertungen.'),
 L('Aufwand vorher (von Hand): ca. 12–16 h je Bericht. Gerechnet wird vorsichtig mit 12 h.'),
 L('Aufwand heute: ca. 1 h für den Bericht (davon ca. 15 Minuten Rückfragen und Nachtragen) plus ca. 1 h erneute Prüfung wegen der Fehler (Schätzung) = ca. 2 h. Durchsicht und Freigabe durch die GF: 15 Minuten.'),
 L([B('Genauigkeit: '),'Korrekturen je Bericht werden ab dem Novemberbericht 2026 gezählt. Ziel nach der Skill-Absicherung: 0.']),
 

 // B2
 H1('2  Daten & Rechtsrahmen'),
 H2('2.1 Datenampel je Schritt'),
 T([0.7,3.2,1.3,4.4],[
  ['Schritt','Daten','Ampel','Begründung'],
  ['1','Termine: Projekt-/Kundenname, Ort, Uhrzeit','Gelb','Firmennamen sind unkritisch. Mitarbeitende stellen ihre Kalender selbst zur Verfügung, den GF-Kalender darf die Assistenz herunterladen.'],
  ['2','Fahrten: Adressen, Zeiten, km','Gelb','Nur Fahrten der GF (die anderen arbeiten fast nur im Büro). Die GF wertet sie selbst aus. Nur mit Team-Account und AVV.'],
  ['4','Stundensätze, km-Satz, Kosten','Rot','Interne Kalkulation. Nur im Bericht, nicht im Wiki, nicht in offenen Tools.'],
  ['4','Stunden je Mitarbeiter und Projekt','Gelb','Nötig für die Kostenrechnung, da die Sätze je Person verschieden sind.'],
  ['4','Auslastung je Mitarbeiter gegenüber Soll','Rot','Leistungskontrolle. Laut GF nicht nötig, entfällt künftig.'],
  ['4','Summen je Projekt ohne Personenbezug','Grün','Aggregierte Kennzahlen.'],
  ['–','Regeln, Kategorien, Prompts','Grün','Verfahrenswissen, darf ins Firmen-Wiki.']],(i,j,c)=>j===2?amp(c):null),
 H2('2.2 Leitfragen'),
 L([B('Werden Kennzahlen pro Person erhoben? '),'Ja, aber nur Stunden je Person und Projekt, weil die Abrechnung sie braucht. Die Auslastungsauswertung je Mitarbeiter wird aus dem Bericht entfernt. Es gibt keinen Betriebsrat, deshalb greift § 87 Abs. 1 Nr. 6 BetrVG nicht. Die DSGVO-Grundsätze Datenminimierung und Transparenz werden eingehalten.']),
 L([B('Greift eine Kennzeichnungspflicht (Art. 50 AI Act)? '),'Nein. Niemand spricht mit einer KI. Der Bericht wird intern erstellt und von einem Menschen freigegeben.']),
 L([B('Rolle und Risikoklasse (KI-VO): '),'Die Firma ist ',B('Betreiber'),', nicht Anbieter: Sie nutzt ein fertiges KI-System für einen internen Zweck. KI zur Leistungsbewertung von Beschäftigten kann hochriskant sein (Anhang III, Beschäftigung). Weil die Auslastung je Mitarbeiter entfällt und keine Entscheidung über Menschen getroffen wird, bleibt der Einsatz eine interne Projektauswertung mit ',B('minimalem Risiko'),'.']),
 L([B('Welche Plattform? '),'Claude Team: Geschäftstarif mit AVV nach Art. 28 DSGVO, ohne Training mit Firmendaten. Laut Datenklassen-Ampel aus Theorietag 18 dürfen Beschäftigtendaten in ein freigegebenes Firmentool nur mit Eintrag im Verarbeitungsverzeichnis und Vertrag, Kalkulationen nur nach Freigabe im Steckbrief (Anhang D). Die Gratis-Version, die im Betrieb teils genutzt wird, ist für diese Daten nicht zulässig. AVV-Umfang und Preis werden vor der Bestellung bei Anthropic bestätigt.']),
 L([B('Ehrlicher Stand: '),'Der Skill wurde in einem Schulungszugang entwickelt und erprobt. Für den Echtbetrieb fehlt ein firmeneigener Zugang mit AVV. ',B('Sofortmaßnahme: '),'Echte Firmendaten werden erst nach Einrichtung des Team-Accounts verarbeitet.']),
 P([I('Keine Rechtsberatung. Im Zweifel wird die oder der Datenschutzbeauftragte hinzugezogen.')]),

 // B3
 H1('3  KI-Einsatzstellen'),
 P('Jede Einsatzstelle hängt an einer offenen Schwachstelle aus Baustein 1 und passt zur Datenampel aus Baustein 2.'),
 T([0.6,0.9,3.6,1.2,1.2,1.4,1.1],[
  ['#','Schwach­stelle','Idee','Art','Stufe','Werkzeug','Ampel'],
  ['E1','S1','Skill absichern: Er nimmt automatisch die zuletzt freigegebene Version. Ein Prüfblatt zeigt, ob die Vormonate unverändert sind und was sich geändert hat.','Prüfung / Muster','Prototyp','Claude Code','Gelb'],
  ['E2','S2','Jede Zuordnung bekommt eine Spalte „warum“. Unsichere Fälle werden gelb markiert statt still zugeordnet.','Muster','Skill','Claude-Skill','Gelb'],
  ['E3','S3','Eine Übersichtsseite für die GF: 5 Kennzahlen plus „Was hat sich zum Vormonat geändert?“','Text','Projekt','Claude-Projekt / Excel','Gelb'],
  ['E4','S4','Fehlende Termine sprechen Berater oder GF per Sprachnotiz ein. Daraus entsteht automatisch eine Nachtragszeile.','Sprache','Prototyp','Handy-Diktat + Claude','Gelb']],(i,j,c)=>j===6?amp(c):null),
 SP(),
 L([B('Nicht offensichtlich: '),'E4 arbeitet mit Sprache, E1 und E2 mit Mustern und Prüflogik. Beides ist keine Textarbeit.']),
 L([B('Bewusst verworfen: '),'Eine Termin-Vorlage, weil die Kurzformen gelöst sind. Ein Vorschlag für die Fahrten-Zuordnung, weil die Fahrerzuordnung gelöst ist. Automatische Rückfrage-Mails, weil Rückfragen nur noch ca. 15 Minuten kosten.']),
 

 // B4
 H1('4  Wirtschaftlichkeit'),
 P([I('Der Business Case aus Theorietag 20 liegt nicht mehr vor. Er wurde hier mit echten Zahlen neu aufgebaut: Arbeitgeberkosten laut Lohnabrechnung und dem gemessenen Aufwand heute.')]),
 P([B('Zeitraum: '),'Jahr 1 sind die ersten 12 Monate ab Einführung des Team-Accounts (Dezember 2026). Die Einrichtung des Skills im Juli 2026 ist trotzdem in Jahr 1 enthalten, das ist vorsichtig gerechnet.']),
 H2('4.1 Interner Stundensatz'),
 P(['Gerechnet wird mit dem ',B('internen Kostensatz von ca. 41 € je Stunde'),'. Das sind die Arbeitgeberkosten (Bruttolohn plus Arbeitgeberanteile zur Sozialversicherung plus Umlagen), geteilt durch die tatsächlich gearbeiteten Stunden (ca. 1.560 h im Jahr nach Urlaub, Feiertagen und Krankheit). Der Verrechnungssatz nach außen ist bewusst nicht verwendet, denn er enthält Gemeinkosten und Gewinn und würde den Nutzen zu hoch ausweisen.']),
 H2('4.2 Kosten und Nutzen'),
 T([3.6,1.5,1.5,3.4],[
  ['Posten','Jahr 1','ab Jahr 2','Herleitung'],
  ['Einrichtung Skill','718 €','–','17,5 h (15–20 h) × 41 €'],
  ['Skill prüfen und absichern (E1/E2)','328 €','–','8 h × 41 €'],
  ['Lizenz Claude Team','1.500 €','1.500 €','Preis lt. claude.com/pricing in USD bestätigt; umgerechnet ca. 25 € je Platz und Monat × 5 Plätze (Worst Case) × 12'],
  ['Auswahl und Schulung','123 €','–','3 h: Account einrichten, Vertretung einweisen'],
  ['Betreuung','246 €','246 €','0,5 h pro Monat'],
  ['Kosten gesamt','2.915 €','1.746 €',''],
  ['Nutzen: gesparte Arbeitszeit','4.920 €','4.920 €','(12 h − 2 h) × 12 Monate × 41 €'],
  ['Ergebnis','+ 2.005 €','+ 3.174 €','']],(i)=>i===6?GREY:(i===8?GRN:null),{right:[1,2],boldRows:[6,8]}),
 P([I('E3 (Übersicht) und E4 (Sprachnotiz) sind in Welle 2 und 3 geplant. Ihr Aufwand wird erst nach dem Test geschätzt und ist noch nicht enthalten. Ebenfalls nicht gerechnet: Entfällt die erneute Prüfung nach E1/E2, spart das weitere ca. 1 h pro Monat (ca. 490 € im Jahr).')],{spacing:{before:100}}),
 H2('4.3 Die Rechenfallen – geprüft'),
 T([2.2,7.4],[
  ['Falle','Wie entschärft'],
  ['Zeit ist nicht Geld','Die gesparten 10 h pro Monat fließen nachweislich in neu übernommene Aufgaben: Vorbereitung von M&A-Angeboten, Inventarauflösung, Buchhaltung und Liquiditätsplanung. Dafür war keine zusätzliche Kraft nötig.'],
  ['Kosten ohne Rechnung','Alle fünf Kostenzeilen sind enthalten, auch die eigene Arbeitszeit für Aufbau, Prüfung, Schulung und Betreuung.'],
  ['Doppelzählung','Die verbleibenden ca. 2 h pro Monat (Bericht und erneute Prüfung) sind in der Ersparnis schon abgezogen und stehen nicht zusätzlich bei den Kosten.'],
  ['Zurechnung','Offen benannt: Der Skill spart Zeit, hat aber Rechenfehler zwischen Versionen mitgebracht (S1, S2). „Vertrauen in die Zahlen“ ist deshalb nicht als Geld gerechnet. Die Lizenz wird voll diesem einen Prozess zugerechnet, obwohl der Account auch anders genutzt wird. Das ist bewusst vorsichtig. Alternative ohne KI geprüft: Excel-Formeln oder Power Query reichen für die freien Kalendertexte nicht (siehe 1.2).'],
  ['Falscher Stundensatz','Interner Kostensatz statt Verrechnungssatz nach außen.']],null,{boldCol0:true}),
 H2('4.4 Unsicherste Annahme'),
 P(['Am unsichersten ist die ',B('Baseline'),', also der Aufwand von früher. Sie ist geschätzt und nicht gemessen. Deshalb hier die Spanne:']),
 T([3,2.2,2.2,2.2],[
  ['Baseline (Aufwand früher)','8 h','12 h (gerechnet)','16 h'],
  ['Ergebnis Jahr 1','+ 37 €','+ 2.005 €','+ 3.973 €'],
  ['Ergebnis ab Jahr 2','+ 1.206 €','+ 3.174 €','+ 5.142 €']],(i,j)=>j===2&&i>0?GRN:null,{boldCol0:true,right:[1,2,3]}),
 P(['Gewinnschwelle: ',B('ab ca. 5,9 h Ersparnis pro Monat'),' im Jahr 1, ab ca. 3,5 h im Dauerbetrieb. Zweitunsicherste Annahme ist der Lizenzpreis. Er macht über die Hälfte der Kosten aus und wird vor der Bestellung geprüft.'],{spacing:{before:120}}),
 H2('4.5 Genauigkeit messbar machen'),
 P(['Die wichtigste Forderung der GF ist ',B('„genauer“'),'. Sie lässt sich nicht in Euro rechnen, aber zählen: ',B('Korrekturen je Bericht'),'. Die Zählung beginnt mit dem Novemberbericht 2026 (Ausgangswert). Ziel nach der Skill-Absicherung: 0 Korrekturen in drei Berichten in Folge.']),

 // B5
 H1('5  Strategie & Einführung'),
 P(['Leitlinie aus dem Gespräch mit der Geschäftsführung: ',B('Genauigkeit vor Tempo'),'. Deshalb wird zuerst abgesichert, was schon läuft, und erst danach erweitert. Alle Kennzahlen beziehen sich auf den Bericht, nie auf eine Person.']),
 H2('5.1 Wellenplan mit Kennzahl und Abbruch'),
 T([1.4,2.4,1.8,2.3,2.1],[
  ['Welle','Wer','Dauer','Kennzahl (je Bericht)','Stopp, wenn …'],
  ['Pilot','Assistenz mit dem abgesicherten Skill (E1, E2) im Team-Account; GF gibt frei','3 Berichte: Nov–Jan (erstellt Dez 2026–Feb 2027)','Korrekturen je Bericht → 0 · Aufwand ≤ 2 h','die Vormonate weiter abweichen'],
  ['Ausweitung','dazu die Kollegin als Vertretung; Übersicht für die GF (E3)','2 Berichte: Feb–Mär (erstellt März–April 2027)','Vertretung erstellt den Bericht ohne Hilfe · Freigabe ≤ 15 Min.','die Vertretung Hilfe braucht oder Korrekturen auftreten'],
  ['Regelbetrieb','monatlich dauerhaft; Sprachnotiz (E4) als Test','ab April 2027','Versand bis zum 5. · 0 Korrekturen','der Jahrescheck im Nov. 2027 negativ ausfällt']],(i,j)=>j===0&&i>0?GREY:null,{boldCol0:true}),
 P([B('Verantwortlich: '),'Die GF entscheidet über Account und Weitergehen nach jeder Welle, die Assistenz setzt um und misst. ',B('Review am 15.03.2027'),' mit der GF: weiter, anpassen oder stoppen. Bei Stopp gilt eine feste Excel-Vorlage mit manueller Fortschreibung, bis die Ursache behoben ist.'],{spacing:{before:120}}),
 P([B('Aufgaben im Pilot: '),'Team-Account einrichten und AVV prüfen · Eintrag im Verarbeitungsverzeichnis · Use-Case-Steckbrief freigeben (Anhang D) · Mini-Richtlinie (5.3) · Skill prüfen und absichern · Auslastung je Mitarbeiter entfernen · Zeit und Korrekturen je Bericht messen.']),
 H2('5.2 Widerstände und Gegenmaßnahmen'),
 T([1.4,3.2,5],[
  ['Wo','Widerstand','Gegenmaßnahme'],
  ['Chef ★','„Ich weiß nicht, ob die Zahlen stimmen.“','Prüfblatt zeigt jeden Monat schwarz auf weiß: Vormonate unverändert, und was sich geändert hat.'],
  ['bei mir ★','„Keine Zeit für die Skill-Prüfung neben den neuen Aufgaben.“','Fester 8-Stunden-Block im Dezember, mit der GF abgestimmt.'],
  ['Chef','„Noch ein Abo, wir haben doch die Gratis-Version.“','In die Gratis-Version dürfen Beschäftigtendaten nicht hinein. Ca. 125 € im Monat stehen gegen 10 gesparte Stunden (ca. 410 €).'],
  ['Team','Berater: „Noch mehr Pflicht.“','Ein Satz per Sprachnotiz statt Nachtrag durch die Assistenz am Monatsende.']],(i,j)=>(i===1||i===2)?'E8F1E4':null,{boldCol0:true}),
 P([I('★ = die zwei wahrscheinlichsten Widerstände')],{spacing:{before:60}}),
 H2('5.3 Richtlinie und Steckbrief'),
 P(['Eine ',B('KI-Nutzungsrichtlinie gibt es in der Firma noch nicht'),'. Der Fall wird deshalb über einen ',B('Use-Case-Steckbrief'),' nach Theorietag 18 abgesichert (Anhang D). Zusätzlich entsteht im Pilot das Minimum für kleine Unternehmen:']),
 L([B('Mini-Richtlinie: '),'Positivliste (freigegeben: Claude Team), Datenklassen-Ampel nach Werkzeug, das Merkblatt mit den sieben Regeln (u. a. keine privaten Accounts, alles nachprüfen, keine Entscheidungen über Menschen automatisieren).']),
 L([B('KI-Register: '),'eine einfache Tabelle mit diesem Use Case als erstem Eintrag.']),
 L([B('Datenschutz: '),'Eintrag im Verarbeitungsverzeichnis, AVV abgelegt, Mitarbeitende informiert.']),
 H2('5.4 Risiken und Gegenmaßnahmen'),
 T([3.2,6.4],[
  ['Risiko','Gegenmaßnahme'],
  ['KI ordnet falsch zu, ohne dass es auffällt','Spalte „warum“ und gelbe Markierung (E2), Prüfblatt Vormonate (E1), Freigabe durch die GF'],
  ['Wissen hängt an einer Person','Skill plus Kurzanleitung, Kollegin als Vertretung eingewiesen'],
  ['Abhängigkeit vom Anbieter','Ergebnis bleibt eine Excel-Datei, Regeln und Daten liegen in der Firma; der Skill ist dokumentiert und gesichert'],
  ['Preisänderung oder Lizenzbedingungen','Review am 15.03.2027; Rechnung bleibt bis ca. 3,5 h Ersparnis pro Monat positiv'],
  ['Datenschutz','Team-Account mit AVV, keine Echtdaten im Schulungszugang, keine Auslastung je Person, Rollen statt Namen im Wiki']],null,{boldCol0:true}),
 H2('5.5 Tool-Empfehlung'),
 P([B('Claude Team'),' für die tägliche Nutzung und den Skill: Geschäftstarif, AVV, kein Training mit Firmendaten, ein Skill für alle Berechtigten. ',B('Claude Code'),' für die Weiterentwicklung und Prüfung des Skills.']),

 // B6
 H1('6  Fazit & Ausblick'),
 box('Kernaussage',[[B('Der Bericht ist schnell, aber noch nicht verlässlich – und das ändern wir zuerst.')]],'E8F1E4'),
 SP(),
 box('Empfehlung',['Ich empfehle einen dreimonatigen Pilot: Team-Account mit AVV, Skill mit Prüfblatt und Begründung je Zuordnung. Ab Jahr 2 bleiben rund 3.200 € im Jahr. Am unsichersten ist der geschätzte Aufwand von früher – aber schon ab 6 Stunden Ersparnis im Monat lohnt es sich. Bis 30.11.2026 entscheidet die Geschäftsführung über den Account; in zwölf Monaten gibt sie den Bericht in 15 Minuten ohne Zweifel frei.']),
 SP(),
 T([2.3,7.3],[
  ['Wann','Was'],
  ['bis 30.11.2026','Entscheidung der GF über den Team-Account (nächster Schritt, in vier Wochen)'],
  ['Dez 2026','Skill-Prüfung, Steckbrief, Verarbeitungsverzeichnis; Pilot startet mit dem Novemberbericht'],
  ['15.03.2027','Review: weiter, anpassen oder stoppen'],
  ['Nov 2027 (in 12 Monaten)','Regelbetrieb: 0 Korrekturen, Vertretung erstellt den Bericht, Freigabe in 15 Minuten, Entscheidung über die Sprachnotiz gefallen']],null,{boldCol0:true}),
 SP(),
 L([B('Was Chef und Team sich merken sollen: '),'Ein KI-Ergebnis ersetzt nicht die Prüfung, erst die eingebaute Kontrolle macht es belastbar. Und: Firmen- und Personaldaten gehören nur in freigegebene Firmentools.']),
 L([B('Ausblick: '),'Dasselbe Muster (Skill plus Prüfblatt) eignet sich für die Zeiterfassung des Teams, aber erst nach einer Datenschutzprüfung, weil dort Gesundheitsdaten anfallen.']),
 H2('Bonus: Würde die KI als kritische Geschäftsführung den Pilot freigeben?'),
 box('Antwort von Claude: Ja, mit Auflagen',[
  'Die Rechnung ist ehrlich, die Fallen sind benannt, es gibt ein Abbruchkriterium – und das Risiko ist klein (ca. 3.000 € Kosten im Jahr 1).',
  [B('Auflage 1: '),'Vor dem ersten Lauf mit echten Daten: Team-Account mit AVV, Steckbrief und Eintrag im Verarbeitungsverzeichnis.'],
  [B('Auflage 2: '),'Skill-Prüfung abgeschlossen, Regressionstest zeigt identische Projektsummen.'],
  [B('Auflage 3: '),'Auslastung je Mitarbeiter entfernt.'],
  [B('Was fehlt: '),'Baseline und Nachprüfung sind geschätzt. Ab dem Novemberbericht Zeit stoppen und Korrekturen zählen – das ist die erste Kennzahl des Pilots.']]),
 H2('Meine Reflexion'),
 L([B('Die KI ist schnell, aber nicht unfehlbar. '),'Beim Aufbau dieses Dokuments hat die KI drei Schwachstellen vermutet (Fahrerzuordnung, Rückfragen, Freigabe), die in Wahrheit längst gelöst waren. Ohne meine Prüfung stünden sie im Bericht. Genau das ist auch die Lehre für den Monatsbericht: Human in the Loop ist kein Misstrauen, sondern Qualitätssicherung.']),
 L([B('Die erste Rechnung war zu schön. '),'Mit dem Verrechnungssatz nach außen wirkte der Nutzen fast viermal so groß. Erst der interne Kostensatz macht die Rechnung ehrlich.']),
 L([B('Das Gespräch mit dem Chef hat die Richtung geändert. '),'Ich dachte, es geht um Zeit. Ihm geht es um Verlässlichkeit. Ohne das Gespräch hätte ich am falschen Ende optimiert.']),
 L([B('Bezahlt heißt nicht freigegeben. '),'Erst beim Abgleich mit Theorietag 18 wurde klar: Ein Schulungszugang ist kein Firmenzugang mit AVV. Deshalb ist der Team-Account keine Kür, sondern Voraussetzung.']),
 BR(),

 // Anhang
 H1('Anhang A – Selbstcheck gegen die Kontrollkriterien'),
 T([1.3,5.6,2.7],[
  ['Baustein','Kriterium','Erfüllt'],
  ['1','Mindestens drei Kandidaten erwogen','✔ vier (1.1)'],
  ['1','Entscheidung begründet','✔ (1.2)'],
  ['1','Ist-Kette gezeichnet, Rollen statt Namen','✔ Swimlane (1.3)'],
  ['1','Mindestens zwei konkrete Schwachstellen','✔ S1–S4 (1.4)'],
  ['1','Eine Zahl zum Prozess','✔ 12–16 h → ca. 2 h'],
  ['2','Mindestens eine Datenkategorie ampelbewertet und begründet','✔ sieben (2.1)'],
  ['2','Kennzahlen am Vorgang, nicht an der Person','✔ Auslastung je MA entfällt'],
  ['2','Kennzeichnung und Plattform geklärt','✔ keine Pflicht · Claude Team mit AVV'],
  ['3','3–5 begründete Einsatzstellen','✔ vier'],
  ['3','Mindestens eine nicht offensichtliche','✔ E4 Sprache, E1/E2 Muster'],
  ['3','Je eine Werkzeug-Idee und Stufe','✔'],
  ['3','Passt zur Datenampel','✔ alle Gelb mit Team-Account'],
  ['4','Echte Zahlen, Schätzungen markiert','✔ Lohnabrechnung, Messung, Baseline als Schätzung'],
  ['4','Jahr 1 und Dauerbetrieb getrennt','✔'],
  ['4','Mindestens eine Falle entschärft','✔ fünf (4.3)'],
  ['4','Ein Ergebnis, auch wenn negativ','✔ positiv, mit Spanne'],
  ['5','Wellenplan mit Kennzahl und Abbruch','✔ Pilot, Ausweitung, Regelbetrieb (5.1)'],
  ['5','Widerstand und Gegenmaßnahme','✔ zwei wahrscheinlichste markiert (5.2)'],
  ['5','Richtlinie geklärt','✔ keine vorhanden → Steckbrief Anhang D + Mini-Richtlinie (5.3)'],
  ['6','Eine Kernaussage','✔ (6)'],
  ['6','Klare Empfehlung','✔ Ja, Pilot über drei Berichte'],
  ['6','Nächster Schritt mit Termin','✔ 30.11.2026 · Ausblick 12 Monate']],(i,j)=>j===2&&i>0?GRN:null),
 H1('Anhang B – So ist das Dokument entstanden'),
 P('Grundlage ist ein eigenes KI-Wiki nach dem LLM-Wiki-Prinzip (Theorietag 21), gepflegt mit Claude Code: Rohdaten in raw/, daraus geordnete Seiten je Baustein mit Inhaltsverzeichnis und Änderungsprotokoll. Lücken wurden mit [offen] markiert und nicht erfunden.'),
 L([B('Arbeitsteilung: '),'Claude hat Kandidaten geprüft, nachgefragt, Ampelfarben und Einsatzstellen vorgeschlagen und gerechnet. Entschieden habe ich: Prozess, Farben, Auswahl der Einsatzstellen, Stundensatz, Wellen.']),
 L([B('Loop Engineering: '),'Die erste Fassung wurde mehrfach nachgeschärft. Drei vermutete Schwachstellen erwiesen sich nach meiner Prüfung als bereits gelöst. Der Stundensatz wurde vom Verrechnungssatz nach außen auf den internen Kostensatz (ca. 41 €) korrigiert.']),
 L([B('Bewährte Prompts: '),'„Du bist meine kritische Geschäftsführung … Entscheide nicht für mich.“ · „Frag bei jeder Zahl: Woher weißt du das?“ · „Ändere nichts ohne Rückfrage.“']),

 H1('Anhang C – Glossar'),
 T([2.2,7.4],[
  ['Begriff','Bedeutung'],
  ['AVV','Auftragsverarbeitungsvertrag nach Art. 28 DSGVO: Der Anbieter darf die Daten nur im Auftrag der Firma verarbeiten, nicht für eigene Zwecke wie KI-Training.'],
  ['Claude','KI-Assistent des Anbieters Anthropic. „Team“ ist der Geschäftstarif mit AVV.'],
  ['Skill','Hinterlegte, wiederholbare Arbeitsanleitung für Claude, hier: wie aus Kalender und Fahrtenbuch der Monatsbericht entsteht.'],
  ['Claude Code','Werkzeug, mit dem Claude direkt an Dateien und Programmen arbeitet; hier zum Prüfen und Verbessern des Skills.'],
  ['Swimlane','Ablaufdarstellung in Bahnen: Jede Bahn ist eine Rolle, die Kästen sind die Schritte.'],
  ['Datenampel','Einstufung von Daten: Grün = unkritisch, Gelb = nur pseudonymisiert oder mit AVV, Rot = nicht in offene KI-Tools.'],
  ['Baseline','Ausgangswert vor der Verbesserung, hier: Aufwand je Bericht von Hand.'],
  ['Human in the Loop','Ein Mensch prüft und gibt frei, bevor ein KI-Ergebnis verwendet wird.'],
  ['KI-Wiki','Eigene Wissenssammlung in Textdateien, die Claude liest und pflegt (Theorietag 21).']],null,{boldCol0:true}),

 BR(),
 H1('Anhang D – Use-Case-Steckbrief (nach Theorietag 18)'),
 T([2.2,7.4],[
  ['Block','Inhalt'],
  ['1 · Identifikation','Monatlicher Projekt-Zeit- und Kostenbericht · Nr. KI-01 · Fachbereich Assistenz der GF · verantwortlich: Assistenz der GF · Stand 11/2026, Version 1. Aus Kalenderexporten und Fahrtenbuch entsteht monatlich ein Excel-Bericht mit Stunden, km und Kosten je Projekt. System: Claude (Anthropic), Tarif Team, als Cloud-Dienst; Skill „projekt-zeit-kosten-report“.'],
  ['2 · KI-VO','Rolle: Betreiber (fertiges System, interner Zweck). Keine verbotene Praxis. Kein Hochrisiko nach Anhang III, da keine Leistungsbewertung oder Entscheidung über Beschäftigte (Auslastung je Person entfällt). Keine Transparenzpflicht nach Art. 50: kein Kundenkontakt, keine Veröffentlichung. Risiko: minimal.'],
  ['3 · Datenschutz','Daten: Kalendertermine (Projekt, Ort, Zeit), Fahrten der GF, Stunden je Person und Projekt. Betroffene: GF, Berater, Assistenz. Keine besonderen Kategorien. Rechtsgrundlage: Durchführung des Beschäftigungsverhältnisses und berechtigtes Interesse an der Projektabrechnung [mit Datenschutz bestätigen]. Eintrag im Verarbeitungsverzeichnis: [offen, im Pilot]. Auftragsverarbeitung: AVV mit Anthropic (Team-Tarif). Drittland: [offen, im AVV prüfen]. Speicherdauer: [offen, nach Aufbewahrungsfristen].'],
  ['4 · Weitere Rechtsgebiete','Stundensätze und Kalkulation sind vertraulich: nur im Team-Account, nicht im Wiki. Mitbestimmung: kein Betriebsrat. Mitarbeitende werden über die Auswertung informiert. Diskriminierungsrisiko: keines, da keine Bewertung von Personen.'],
  ['5 · Betrieb und Kontrolle','Menschliche Aufsicht: Assistenz prüft (Prüfblatt, gelbe Fälle), GF gibt jeden Bericht frei. Kennzahlen: Korrekturen und Aufwand je Bericht. Vertretung eingewiesen. Wiedervorlage: Review 15.03.2027, danach jährlich.'],
  ['6 · Entscheidung','Vorschlag: Freigabe mit Auflagen – Team-Account mit AVV, Eintrag im Verarbeitungsverzeichnis, keine Echtdaten vorher. Unterschrift GF: ______________ Datum: ________ Nächste Überprüfung: 15.03.2027']],null,{boldCol0:true}),
];

const doc=new Document({
 styles:{default:{document:{run:{font:'Arial',size:20}}},
  paragraphStyles:[
   {id:'Heading1',name:'Heading 1',basedOn:'Normal',next:'Normal',quickFormat:true,run:{font:'Arial',size:30,bold:true,color:HEAD},paragraph:{spacing:{before:320,after:140},keepNext:true,outlineLevel:0}},
   {id:'Heading2',name:'Heading 2',basedOn:'Normal',next:'Normal',quickFormat:true,run:{font:'Arial',size:22,bold:true,color:ACC},paragraph:{spacing:{before:220,after:90},keepNext:true,outlineLevel:1}}]},
 numbering:{config:[{reference:'b',levels:[{level:0,format:LevelFormat.BULLET,text:'•',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:360,hanging:260}}}}]},
   {reference:'n',levels:[{level:0,format:LevelFormat.DECIMAL,text:'%1.',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:360,hanging:260}}}}]}]},
 sections:[{properties:{page:{margin:{top:1134,bottom:1134,left:1134,right:1134}},titlePage:true},
  footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.RIGHT,children:[new TextRun({text:'Praxisprojekt KI-Schulung · Seite ',size:16,color:'777777'}),new TextRun({children:[PageNumber.CURRENT],size:16,color:'777777'})]})]}),first:new Footer({children:[new Paragraph('')]})},
  children:kids}]});
Packer.toBuffer(doc).then(b=>fs.writeFileSync(process.argv[2],b));
