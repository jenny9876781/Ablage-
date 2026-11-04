const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,WidthType,ShadingType,HeadingLevel,AlignmentType,LevelFormat,PageBreak,Footer,PageNumber,BorderStyle,VerticalAlign}=require('docx');
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
 box('Das Problem',[ 'Jeden Monat werden Kalendertermine und Fahrten zu Kosten je Projekt zusammengeführt. Von Hand dauerte das 12–16 Stunden. Seit Juli 2026 erledigt ein Claude-Skill das in etwa einer Stunde. Damit ist das Tempo-Problem gelöst, aber ein neues ist entstanden: Die Geschäftsführung ist nicht sicher, ob der Bericht stimmt. Zwischen Versionen weichen Vormonate ab, Zuordnungen waren teils falsch, und der Bericht ist unübersichtlich.']),
 SP(),
 T([3,3,3],[['Zeit je Bericht','Ergebnis pro Jahr','Lohnt sich ab'],['früher 12–16 h · heute 1 h','Jahr 1: +2.497 € · ab Jahr 2: +3.666 €','5,9 h Ersparnis pro Monat (gemessen: 11 h)']],(i)=>i===1?'DCEAF2':null,{boldRows:[1]}),
 SP(),
 box('Empfehlung',[[B('1. '),'Einen Claude-Team-Account für die Firma einrichten: Geschäftstarif mit Auftragsverarbeitungsvertrag (AVV) statt der Gratis-Version.'],[B('2. '),'Den bestehenden Skill im Dezember mit Claude Code prüfen und absichern: feste Versionsregel, Prüfblatt für die Vormonate, Begründung je Zuordnung.'],[B('3. '),'Die Auswertung „Auslastung je Mitarbeiter“ aus dem Bericht entfernen.']],'E8F1E4'),
 SP(),
 box('Nächster Schritt',['Entscheidung der Geschäftsführung über den Team-Account bis 30.11.2026. Danach dient der Novemberbericht als Testfall für den abgesicherten Skill.']),
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
 H2('1.3 Ist-Kette als Swimlane (Rot = Schwachstelle)'),
 T([1.6,1,1,1,1.1,1.1,1.1,1,1.1,0.9],sw,swShade,{boldCol0:true}),
 SP(),
 T([0.5,3.2,1.5,1.7,3.2],[
  ['#','Schritt','Rolle','Werkzeug','Status heute'],
  ['1','Termin mit Projektname im Betreff eintragen','GF, Berater','Outlook','S1: fehlende Termine trägt die Assistenz händisch nach · Kurzformen gelöst'],
  ['2','Fahrt wird aufgezeichnet (praktisch nur GF)','GF','Fahrtenbuch-App','gelöst: feste Zuordnung Fahrzeug → Fahrer im Skill'],
  ['3','Monatsende: Kalender und Fahrten exportieren','Assistenz','Outlook, App','–'],
  ['4','Bericht erzeugen (Fahrt ↔ Termin, Kosten je Zeile)','Assistenz','Claude-Skill → Excel','S5a: ältere gespeicherte Excel statt zuletzt bearbeiteter als Vorlage → Vormonate weichen ab'],
  ['5','Unklare Fälle prüfen','Assistenz','Excel','S5b: falsche Zuordnungen, erst bei erneuter Prüfung entdeckt · Rückfragen nur noch ca. 15 Min.'],
  ['6','Fehlende Zeiten und Zusatzkosten nachtragen','Assistenz','Excel','S1 (siehe Schritt 1)'],
  ['7','Zuordnungstabellen pflegen','Assistenz','Excel','–'],
  ['8','Durchsicht und Freigabe','GF','Excel / Mail','S5c: unübersichtlich, GF unsicher, ob es stimmt · Freigabe nur 15 Min.'],
  ['9','Versand an Partnerfirma / Abrechnung','Assistenz','Mail','meist bis zum 5. des Folgemonats']],(i,j,c)=>j===4&&/S\d/.test(c)?RED:(j===4&&/gelöst/.test(c)?GRN:null)),
 H2('1.4 Was die KI schon gelöst hat – und was nicht'),
 L([B('Gelöst durch den Skill: '),'Rechenzeit (von 12–16 h auf 1 h), falsche Fahrerzuordnung, uneinheitliche Projektkurzformen, lange Rückfrage-Schleifen, Freigabe-Stau.']),
 L([B('Noch offen: '),'S1 fehlende Termine, S5a falsche Vorlage, S5b falsche Zuordnungen, S5c unübersichtlicher Bericht. Kurz: Das Tempo stimmt, die ',B('Genauigkeit'),' noch nicht.']),
 L([B('Aus dem Gespräch mit der Geschäftsführung (04.11.2026): '),'„Der Bericht ist zu unübersichtlich, und man ist sich nicht sicher, ob er stimmt.“ Gewünscht ist: ',B('genauer'),', nicht schneller.']),
 H2('1.5 Zahl zum Prozess'),
 L('12 Monatsberichte im Jahr, dazu Jahresauswertungen.'),
 L('Aufwand vorher (von Hand): ca. 12–16 h je Bericht. Gerechnet wird vorsichtig mit 12 h.'),
 L('Aufwand heute: höchstens 1 h, davon ca. 15 Minuten Rückfragen und Nachtragen. Durchsicht und Freigabe durch die GF: 15 Minuten.'),
 

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
 L([B('Welche Plattform? '),'Claude Team: Geschäftstarif mit AVV nach Art. 28 DSGVO, ohne Training mit Firmendaten. Die Gratis-Version, die im Betrieb teils genutzt wird, ist für diese Daten nicht zulässig. AVV-Umfang und Preis werden vor der Bestellung bei Anthropic bestätigt.']),
 P([I('Keine Rechtsberatung. Im Zweifel wird die oder der Datenschutzbeauftragte hinzugezogen.')]),

 // B3
 H1('3  KI-Einsatzstellen'),
 P('Jede Einsatzstelle hängt an einer offenen Schwachstelle aus Baustein 1 und passt zur Datenampel aus Baustein 2.'),
 T([0.6,0.9,3.6,1.2,1.2,1.4,1.1],[
  ['#','Schwach­stelle','Idee','Art','Stufe','Werkzeug','Ampel'],
  ['E6','S5a','Skill absichern: Er nimmt automatisch die zuletzt freigegebene Version. Ein Prüfblatt zeigt, ob die Vormonate unverändert sind und was sich geändert hat.','Prüfung / Muster','Prototyp','Claude Code','Gelb'],
  ['E7','S5b','Jede Zuordnung bekommt eine Spalte „warum“. Unsichere Fälle werden gelb markiert statt still zugeordnet.','Muster','Skill','Claude-Skill','Gelb'],
  ['E3','S1','Fehlende Termine sprechen Berater oder GF per Sprachnotiz ein. Daraus entsteht automatisch eine Nachtragszeile.','Sprache','Prototyp','Handy-Diktat + Claude','Gelb'],
  ['E5','S5c','Eine Übersichtsseite für die GF: 5 Kennzahlen plus „Was hat sich zum Vormonat geändert?“','Text','Projekt','Claude-Projekt / Excel','Gelb']],(i,j,c)=>j===6?amp(c):null),
 SP(),
 L([B('Nicht offensichtlich: '),'E3 arbeitet mit Sprache, E6 und E7 mit Mustern und Prüflogik. Beides ist keine Textarbeit.']),
 L([B('Bewusst verworfen: '),'Eine Termin-Vorlage, weil die Kurzformen gelöst sind. Ein Vorschlag für die Fahrten-Zuordnung, weil die Fahrerzuordnung gelöst ist. Automatische Rückfrage-Mails, weil Rückfragen nur noch ca. 15 Minuten kosten.']),
 

 // B4
 H1('4  Wirtschaftlichkeit'),
 P([I('Der Business Case aus Theorietag 20 liegt nicht mehr vor. Er wurde hier mit echten Zahlen neu aufgebaut: Arbeitgeberkosten laut Lohnabrechnung und dem gemessenen Aufwand heute.')]),
 H2('4.1 Interner Stundensatz'),
 P(['Gerechnet wird mit dem ',B('internen Kostensatz von ca. 41 € je Stunde'),'. Das sind die Arbeitgeberkosten (Bruttolohn plus Arbeitgeberanteile zur Sozialversicherung plus Umlagen), geteilt durch die tatsächlich gearbeiteten Stunden (ca. 1.560 h im Jahr nach Urlaub, Feiertagen und Krankheit). Der Verrechnungssatz nach außen ist bewusst nicht verwendet, denn er enthält Gemeinkosten und Gewinn und würde den Nutzen zu hoch ausweisen.']),
 H2('4.2 Kosten und Nutzen'),
 T([3.6,1.5,1.5,3.4],[
  ['Posten','Jahr 1','ab Jahr 2','Herleitung'],
  ['Einrichtung Skill','718 €','–','17,5 h (15–20 h) × 41 €'],
  ['Skill prüfen und absichern (E6/E7)','328 €','–','8 h × 41 €'],
  ['Lizenz Claude Team','1.500 €','1.500 €','ca. 25 € je Platz und Monat × 5 Plätze (Worst Case Mindestabnahme) × 12'],
  ['Auswahl und Schulung','123 €','–','3 h: Account einrichten, Vertretung einweisen'],
  ['Betreuung','246 €','246 €','0,5 h pro Monat'],
  ['Kosten gesamt','2.915 €','1.746 €',''],
  ['Nutzen: gesparte Arbeitszeit','5.412 €','5.412 €','(12 h − 1 h) × 12 Monate × 41 €'],
  ['Ergebnis','+ 2.497 €','+ 3.666 €','']],(i)=>i===6?GREY:(i===8?GRN:null),{right:[1,2],boldRows:[6,8]}),
 P([I('E3 (Sprachnotiz) und E5 (Übersicht) sind in Welle 2 und 3 geplant. Ihr Aufwand wird erst nach dem Test geschätzt und ist in der Rechnung noch nicht enthalten.')],{spacing:{before:100}}),
 H2('4.3 Die Rechenfallen – geprüft'),
 T([2.2,7.4],[
  ['Falle','Wie entschärft'],
  ['Zeit ist nicht Geld','Die gesparten 11 h pro Monat fließen nachweislich in neu übernommene Aufgaben: Vorbereitung von M&A-Angeboten, Inventarauflösung, Buchhaltung und Liquiditätsplanung. Dafür war keine zusätzliche Kraft nötig.'],
  ['Kosten ohne Rechnung','Alle fünf Kostenzeilen sind enthalten, auch die eigene Arbeitszeit für Aufbau, Prüfung, Schulung und Betreuung.'],
  ['Doppelzählung','Die verbleibende Stunde pro Monat ist in der Ersparnis schon abgezogen und steht nicht zusätzlich bei den Kosten.'],
  ['Zurechnung','Offen benannt: Der Skill spart Zeit, hat aber Rechenfehler zwischen Versionen mitgebracht (S5). „Vertrauen in die Zahlen“ ist deshalb nicht als Geld gerechnet. Die Lizenz wird voll diesem einen Prozess zugerechnet, obwohl der Account auch anders genutzt wird. Das ist bewusst vorsichtig.'],
  ['Falscher Stundensatz','Interner Kostensatz statt Verrechnungssatz nach außen.']],null,{boldCol0:true}),
 H2('4.4 Unsicherste Annahme'),
 P(['Am unsichersten ist die ',B('Baseline'),', also der Aufwand von früher. Sie ist geschätzt und nicht gemessen. Deshalb hier die Spanne:']),
 T([3,2.2,2.2,2.2],[
  ['Baseline (Aufwand früher)','8 h','12 h (gerechnet)','16 h'],
  ['Ergebnis Jahr 1','+ 529 €','+ 2.497 €','+ 4.465 €'],
  ['Ergebnis ab Jahr 2','+ 1.698 €','+ 3.666 €','+ 5.634 €']],(i,j)=>j===2&&i>0?GRN:null,{boldCol0:true,right:[1,2,3]}),
 P(['Gewinnschwelle: ',B('ab ca. 5,9 h Ersparnis pro Monat'),' im Jahr 1, ab ca. 3,5 h im Dauerbetrieb. Zweitunsicherste Annahme ist der Lizenzpreis. Er macht über die Hälfte der Kosten aus und wird vor der Bestellung geprüft.'],{spacing:{before:120}}),
 

 // B5
 H1('5  Strategie & Einführung'),
 P(['Leitlinie aus dem Gespräch mit der Geschäftsführung: ',B('Genauigkeit vor Tempo'),'. Deshalb wird zuerst abgesichert, was schon läuft, und erst danach erweitert.']),
 H2('5.1 Wellenplan'),
 T([1,1.6,4.8,2.2],[
  ['Welle','Zeitraum','Inhalt','Verantwortlich'],
  ['1','Nov–Dez 2026','Claude-Team-Account einrichten, AVV prüfen. Kurze Regel aufstellen, welche Daten in die KI dürfen (ersetzt die ungeregelte Gratis-Nutzung). E6/E7: Skill mit Claude Code prüfen und absichern, dabei die Auslastung je Mitarbeiter entfernen.','GF entscheidet, Assistenz setzt um'],
  ['2','Jan–Feb 2027','Kollegin als Vertretung einweisen (GF hat zugestimmt). E5: Übersichtsseite für die GF.','Assistenz'],
  ['3','ab März 2027','E3: Nachmeldung per Sprachnotiz testen (GF hat zugesagt). Danach entscheiden: ausrollen oder lassen.','GF, Berater, Assistenz']]),
 P([B('Erfolgskriterium Welle 1: '),'drei Monatsberichte in Folge ohne Abweichung in den Vormonaten. Die Freigabe bleibt bei höchstens 15 Minuten.'],{spacing:{before:120}}),
 H2('5.2 Widerstände und Konter'),
 T([4.3,5.3],[
  ['Widerstand','Konter'],
  ['GF: „Ich weiß nicht, ob die Zahlen stimmen.“','Das Prüfblatt zeigt jeden Monat schwarz auf weiß: Vormonate unverändert, und was sich geändert hat.'],
  ['„Noch ein Abo, wir haben doch die Gratis-Version.“','In die Gratis-Version dürfen Daten von Beschäftigten nicht hinein. Ca. 125 € im Monat stehen gegen 11 gesparte Stunden (ca. 450 €).'],
  ['Berater: „Noch mehr Pflicht.“','Ein Satz per Sprachnotiz statt Nachtrag durch die Assistenz am Monatsende.'],
  ['„Wenn die Assistenz ausfällt, kann es keiner.“','Skill plus Kurzanleitung: Die Kollegin übernimmt (GF hat zugestimmt).']],null,{boldCol0:false}),
 H2('5.3 Tool-Empfehlung'),
 P([B('Claude Team'),' für die tägliche Nutzung und den Skill: Geschäftstarif, AVV, kein Training mit Firmendaten, ein Skill für alle Berechtigten. ',B('Claude Code'),' für die Weiterentwicklung und Prüfung des Skills.']),

 // B6
 H1('6  Fazit & Ausblick'),
 box('Kernbotschaft',[[B('Die KI hat aus 12–16 Stunden Handarbeit eine Stunde gemacht. Jetzt geht es nicht mehr um Tempo, sondern um Vertrauen in die Zahlen.')]],'E8F1E4'),
 SP(),
 L([B('Empfehlung: '),'Claude-Team-Account einrichten und den Skill im Dezember mit Claude Code absichern. Die Rechnung ist auch vorsichtig gerechnet positiv: +2.497 € im ersten Jahr, +3.666 € ab dem zweiten.']),
 L([B('Nächster Schritt: '),'Die GF entscheidet bis 30.11.2026 über den Team-Account. Der Novemberbericht ist der erste Testfall.']),
 L([B('Was Chef und Team sich merken sollen: '),'Ein KI-Ergebnis ersetzt nicht die Prüfung. Erst die eingebaute Kontrolle macht es belastbar. Und: In die Gratis-Version gehören keine Firmen- und Personaldaten.']),
 L([B('Ausblick: '),'Dasselbe Muster (Skill plus Prüfblatt) eignet sich für die Zeiterfassung des Teams, aber erst nach einer Datenschutzprüfung, weil dort Gesundheitsdaten anfallen.']),
 BR(),

 // Anhang
 H1('Anhang A – Selbstcheck gegen die Kontrollkriterien'),
 T([1.3,5.6,2.7],[
  ['Baustein','Kriterium','Erfüllt'],
  ['1','Mindestens drei Kandidaten erwogen','✔ vier (1.1)'],
  ['1','Entscheidung begründet','✔ (1.2)'],
  ['1','Ist-Kette gezeichnet, Rollen statt Namen','✔ Swimlane (1.3)'],
  ['1','Mindestens zwei konkrete Schwachstellen','✔ S1, S5a, S5b, S5c'],
  ['1','Eine Zahl zum Prozess','✔ 12–16 h → 1 h'],
  ['2','Mindestens eine Datenkategorie ampelbewertet und begründet','✔ sieben (2.1)'],
  ['2','Kennzahlen am Vorgang, nicht an der Person','✔ Auslastung je MA entfällt'],
  ['2','Kennzeichnung und Plattform geklärt','✔ keine Pflicht · Claude Team mit AVV'],
  ['3','3–5 begründete Einsatzstellen','✔ vier'],
  ['3','Mindestens eine nicht offensichtliche','✔ E3 Sprache, E6/E7 Muster'],
  ['3','Je eine Werkzeug-Idee und Stufe','✔'],
  ['3','Passt zur Datenampel','✔ alle Gelb mit Team-Account'],
  ['4','Echte Zahlen, Schätzungen markiert','✔ Lohnabrechnung, Messung, Baseline als Schätzung'],
  ['4','Jahr 1 und Dauerbetrieb getrennt','✔'],
  ['4','Mindestens eine Falle entschärft','✔ fünf'],
  ['4','Ein Ergebnis, auch wenn negativ','✔ positiv, mit Spanne'],
  ['5','Einführungsplan in Wellen mit Gegenmaßnahmen','✔ drei Wellen, vier Konter'],
  ['6','Klare Empfehlung mit nächstem Schritt','✔ Entscheidung bis 30.11.2026']],(i,j)=>j===2&&i>0?GRN:null),
 H1('Anhang B – So ist das Dokument entstanden'),
 P('Grundlage ist ein eigenes KI-Wiki nach dem LLM-Wiki-Prinzip (Theorietag 21), gepflegt mit Claude Code: Rohdaten in raw/, daraus geordnete Seiten je Baustein mit Inhaltsverzeichnis und Änderungsprotokoll. Lücken wurden mit [offen] markiert und nicht erfunden.'),
 L([B('Arbeitsteilung: '),'Claude hat Kandidaten geprüft, nachgefragt, Ampelfarben und Einsatzstellen vorgeschlagen und gerechnet. Entschieden habe ich: Prozess, Farben, Auswahl der Einsatzstellen, Stundensatz, Wellen.']),
 L([B('Loop Engineering: '),'Die erste Fassung wurde mehrfach nachgeschärft. Drei vermutete Schwachstellen erwiesen sich nach meiner Prüfung als bereits gelöst. Der Stundensatz wurde vom Verrechnungssatz (150 €) auf den internen Kostensatz (41 €) korrigiert.']),
 L([B('Bewährte Prompts: '),'„Du bist meine kritische Geschäftsführung … Entscheide nicht für mich.“ · „Frag bei jeder Zahl: Woher weißt du das?“ · „Ändere nichts ohne Rückfrage.“']),
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
