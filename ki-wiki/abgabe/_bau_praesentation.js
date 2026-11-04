const pptxgen=require('pptxgenjs');
const SK='/root/.claude/skills/synced/2b435a0a-2155-4876-8b8d-3165a34d3deb_a34d83bc-f2b5-4b94-a132-3831f802c742/pptx';
const {applyTheme}=require(SK+'/scripts/apply_theme.js');
const THEME={name:'Monatsbericht',headFontFace:'Cambria',bodyFontFace:'Calibri',colors:{dk1:'1B2B36',lt1:'FFFFFF',dk2:'1F3A4D',lt2:'EEF3F6',accent1:'2E6E8E',accent2:'D9644A',accent3:'3E8E5E',accent4:'E0A526',accent5:'8AA9BA',accent6:'5B6B75',hlink:'2E6E8E',folHlink:'5B6B75'}};
const HX={navy:'1F3A4D',teal:'2E6E8E',coral:'D9644A',green:'3E8E5E',amber:'E0A526',light:'EEF3F6',grey:'5B6B75'};
const pres=new pptxgen(); pres.layout='LAYOUT_WIDE'; pres.theme={headFontFace:THEME.headFontFace,bodyFontFace:THEME.bodyFontFace};
pres.title='Vom schnellen zum verlässlichen Monatsbericht'; pres.author='Jennifer Preisigke';
const C=pres.SchemeColor;
pres.defineSlideMaster({title:'DARK',background:{color:HX.navy},objects:[
 {placeholder:{options:{name:'title',type:'title',x:0.8,y:2.2,w:11.7,h:1.6,fontSize:44,bold:true,color:C.background1,valign:'bottom',align:'left'},text:''}},
 {placeholder:{options:{name:'body',type:'body',x:0.8,y:4.0,w:11.7,h:2.0,fontSize:20,color:C.accent5,align:'left',valign:'top'},text:''}}]});
pres.defineSlideMaster({title:'CONTENT',background:{color:'FFFFFF'},objects:[
 {placeholder:{options:{name:'title',type:'title',x:0.6,y:0.4,w:12.1,h:0.9,fontSize:34,bold:true,color:C.text2,valign:'top',align:'left'},text:''}},
 {text:{text:'Praxisprojekt KI-Schulung · Monatsbericht',options:{x:0.6,y:7.0,w:8,h:0.3,fontSize:10,color:C.accent6}}}],
 slideNumber:{x:12.2,y:7.0,w:0.6,h:0.3,fontSize:10,color:C.accent6}});
const add=(m,sec)=>pres.addSlide({masterName:m,sectionTitle:sec});
const tb=(s,t,o)=>s.addText(t,{isTextBox:true,margin:0,fontSize:16,color:C.text1,...o});
const card=(s,x,y,w,h,fill)=>s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w,h,rectRadius:0.12,fill:{color:fill},line:{color:fill}});
const circ=(s,x,y,d,fill,t)=>{s.addShape(pres.shapes.OVAL,{x,y,w:d,h:d,fill:{color:fill},line:{color:fill}});tb(s,t,{x,y,w:d,h:d,align:'center',valign:'middle',bold:true,fontSize:14,color:C.background1});};

// 1 Titel
pres.addSection({title:'Einstieg'});
let s=add('DARK','Einstieg');
s.addText('Vom schnellen zum verlässlichen Monatsbericht',{placeholder:'title'});
s.addText('KI im Projekt-Zeit- und Kostenbericht · Praxisprojekt KI-Schulung · Jennifer Preisigke · November 2026',{placeholder:'body'});
s.addNotes('Kurzfassung des Abschlussberichts. Alle Zahlen identisch mit dem Word-Bericht.');

// 2 Problem
s=add('CONTENT','Einstieg'); s.addText('Das Tempo ist gelöst – das Vertrauen noch nicht',{placeholder:'title'});
card(s,0.6,1.6,3.8,4.9,C.background2);
tb(s,'früher von Hand',{x:0.9,y:1.9,w:3.2,h:0.4,fontSize:14,color:C.accent6});
tb(s,'12–16 h',{x:0.9,y:2.3,w:3.2,h:1.0,fontSize:54,bold:true,color:C.accent2,fontFace:'Cambria'});
tb(s,'heute mit Claude-Skill',{x:0.9,y:3.6,w:3.2,h:0.4,fontSize:14,color:C.accent6});
tb(s,'1 h',{x:0.9,y:4.0,w:3.2,h:1.0,fontSize:54,bold:true,color:C.accent3,fontFace:'Cambria'});
tb(s,'je Monatsbericht',{x:0.9,y:5.4,w:3.2,h:0.4,fontSize:14,color:C.accent6});
tb(s,'„Der Bericht ist zu unübersichtlich, und man ist sich nicht sicher, ob er stimmt.“',{x:4.9,y:1.6,w:7.8,h:0.9,fontSize:20,italic:true,color:C.text2});
tb(s,'Geschäftsführung, Gespräch 04.11.2026',{x:4.9,y:2.5,w:7.8,h:0.3,fontSize:12,color:C.accent6});
const probs=[['S5a','Falsche Vorlage: ältere Excel statt der zuletzt bearbeiteten – Vormonate weichen ab'],['S5b','Falsche Zuordnungen, erst bei erneuter Prüfung entdeckt'],['S5c','Bericht unübersichtlich – Freigabe ohne Sicherheit'],['S1','Fehlende Termine werden von Hand nachgetragen']];
probs.forEach((p,i)=>{const y=3.1+i*0.85;circ(s,4.9,y,0.6,HX.coral,p[0]);tb(s,p[1],{x:5.7,y,w:7.0,h:0.6,valign:'middle'});});

// 3 Ist-Kette
pres.addSection({title:'Analyse'});
s=add('CONTENT','Analyse'); s.addText('Ist-Kette: neun Schritte, vier offene Stellen',{placeholder:'title'});
const steps=[['Termin eintragen','GF/Berater','S1'],['Fahrt erfassen','GF','ok'],['Export','Assistenz',''],['Bericht erzeugen','Skill','S5a'],['Prüfen','Assistenz','S5b'],['Nachtragen','Assistenz','S1'],['Pflege','Assistenz',''],['Freigabe','GF','S5c'],['Versand','Assistenz','']];
const bw=1.28,gap=0.08;
steps.forEach((st,i)=>{const x=0.6+i*(bw+gap),y=2.0;const fill=st[2].startsWith('S')?HX.coral:(st[2]==='ok'?HX.green:HX.teal);
 card(s,x,y,bw,1.7,fill);tb(s,String(i+1),{x:x+0.12,y:y+0.1,w:0.5,h:0.35,fontSize:14,bold:true,color:C.background1});
 tb(s,st[0],{x:x+0.12,y:y+0.5,w:bw-0.2,h:0.7,fontSize:14,bold:true,color:C.background1,valign:'top'});
 tb(s,st[1]+(st[2].startsWith('S')?' · '+st[2]:''),{x:x+0.12,y:y+1.25,w:bw-0.2,h:0.35,fontSize:11,color:C.background1});});
card(s,0.6,4.3,5.9,2.3,C.background2);
tb(s,'Gelöst durch den Skill',{x:0.9,y:4.5,w:5.4,h:0.4,fontSize:18,bold:true,color:C.accent3});
tb(s,[{text:'Rechenzeit 12–16 h → 1 h',options:{bullet:true,breakLine:true}},{text:'Fahrerzuordnung, Projekt-Kurzformen',options:{bullet:true,breakLine:true}},{text:'Rückfragen und Freigabe je ca. 15 Min.',options:{bullet:true}}],{x:0.9,y:5.0,w:5.4,h:1.4,paraSpaceAfter:6});
card(s,6.8,4.3,5.9,2.3,C.background2);
tb(s,'Noch offen: Genauigkeit',{x:7.1,y:4.5,w:5.4,h:0.4,fontSize:18,bold:true,color:C.accent2});
tb(s,[{text:'S5a falsche Vorlage · S5b falsche Zuordnung',options:{bullet:true,breakLine:true}},{text:'S5c unübersichtlich',options:{bullet:true,breakLine:true}},{text:'S1 fehlende Termine',options:{bullet:true}}],{x:7.1,y:5.0,w:5.4,h:1.4,paraSpaceAfter:6});

// 4 Daten
s=add('CONTENT','Analyse'); s.addText('Daten & Recht: nur so viel Personenbezug wie nötig',{placeholder:'title'});
const amp=[[HX.green,'Grün','Projektsummen ohne Personenbezug · Regeln, Kategorien, Prompts'],[HX.amber,'Gelb','Termine (von Mitarbeitenden selbst geliefert) · Fahrten nur der GF · Stunden je Person und Projekt für die Abrechnung'],[HX.coral,'Rot','Stundensätze und Kalkulation – nur im Bericht · Auslastung je Mitarbeiter – entfällt']];
amp.forEach((a,i)=>{const x=0.6+i*4.1;card(s,x,1.6,3.9,3.2,C.background2);s.addShape(pres.shapes.OVAL,{x:x+0.3,y:1.9,w:0.7,h:0.7,fill:{color:a[0]},line:{color:a[0]}});
 tb(s,a[1],{x:x+1.2,y:1.9,w:2.4,h:0.7,fontSize:22,bold:true,valign:'middle'});tb(s,a[2],{x:x+0.3,y:2.8,w:3.3,h:1.9,valign:'top'});});
card(s,0.6,5.1,12.1,1.5,C.background2);
tb(s,[{text:'Plattform: ',options:{bold:true}},{text:'Claude Team mit Auftragsverarbeitungsvertrag (AVV) statt Gratis-Version. ',options:{}},{text:'Kennzeichnungspflicht: ',options:{bold:true}},{text:'keine (keine KI im Kundenkontakt). ',options:{}},{text:'Betriebsrat: ',options:{bold:true}},{text:'keiner – Datenminimierung nach DSGVO trotzdem eingehalten.',options:{}}],{x:0.9,y:5.25,w:11.5,h:1.2,valign:'middle'});

// 5 Einsatzstellen
pres.addSection({title:'Lösung'});
s=add('CONTENT','Lösung'); s.addText('Vier KI-Einsatzstellen – jede an einer Schwachstelle',{placeholder:'title'});
const es=[['E6','Skill absichern','Immer die letzte freigegebene Version; Prüfblatt „Vormonate unverändert?“','S5a · Claude Code · Prototyp'],['E7','Spalte „warum“','Jede Zuordnung begründet, unsichere Fälle gelb statt still zugeordnet','S5b · Muster · Skill'],['E3','Sprachnotiz','Fehlende Termine einsprechen → automatische Nachtragszeile','S1 · Sprache · Prototyp'],['E5','Chef-Übersicht','5 Kennzahlen + „Was hat sich zum Vormonat geändert?“','S5c · Text · Projekt']];
es.forEach((e,i)=>{const x=0.6+(i%2)*6.15,y=1.6+Math.floor(i/2)*2.6;card(s,x,y,5.95,2.35,C.background2);circ(s,x+0.3,y+0.3,0.8,HX.teal,e[0]);
 tb(s,e[1],{x:x+1.3,y:y+0.3,w:4.4,h:0.5,fontSize:20,bold:true,color:C.text2});tb(s,e[2],{x:x+1.3,y:y+0.85,w:4.4,h:0.9,valign:'top'});tb(s,e[3],{x:x+1.3,y:y+1.8,w:4.4,h:0.35,fontSize:12,color:C.accent6});});

// 6 Wirtschaftlichkeit
s=add('CONTENT','Lösung'); s.addText('Vorsichtig gerechnet – und trotzdem positiv',{placeholder:'title'});
s.addChart(pres.charts.BAR,[{name:'Kosten',labels:['Jahr 1','ab Jahr 2'],values:[2915,1746]},{name:'Nutzen',labels:['Jahr 1','ab Jahr 2'],values:[5412,5412]}],
 {x:0.6,y:1.5,w:6.6,h:5.1,barDir:'col',barGrouping:'clustered',chartColors:[HX.coral,HX.green],showValue:true,dataLabelPosition:'outEnd',dataLabelFormatCode:'#,##0 "€"',dataLabelFontSize:12,dataLabelFontFace:'+mn-lt',
  showLegend:true,legendPos:'b',legendFontFace:'+mn-lt',legendFontSize:12,catAxisLabelFontFace:'+mn-lt',catAxisLabelFontSize:14,catAxisLabelColor:HX.grey,valAxisHidden:true,valGridLine:{style:'none'},catGridLine:{style:'none'},showTitle:false});
tb(s,'Ergebnis Jahr 1',{x:7.7,y:1.6,w:5,h:0.4,fontSize:14,color:C.accent6});
tb(s,'+2.497 €',{x:7.7,y:2.0,w:5,h:0.9,fontSize:48,bold:true,color:C.accent3,fontFace:'Cambria'});
tb(s,'ab Jahr 2',{x:7.7,y:3.0,w:5,h:0.4,fontSize:14,color:C.accent6});
tb(s,'+3.666 € / Jahr',{x:7.7,y:3.4,w:5,h:0.9,fontSize:40,bold:true,color:C.accent3,fontFace:'Cambria'});
card(s,7.7,4.55,5.0,2.05,C.background2);
tb(s,[{text:'Interner Kostensatz 41 €/h',options:{bullet:true,breakLine:true}},{text:'Gesparte 11 h/Monat fließen in M&A, Buchhaltung, Liquiplanung',options:{bullet:true,breakLine:true}},{text:'Lohnt ab 5,9 h Ersparnis/Monat',options:{bullet:true}}],{x:7.95,y:4.7,w:4.6,h:1.8,fontSize:14,paraSpaceAfter:4});

// 7 Einführung
s=add('CONTENT','Lösung'); s.addText('Drei Wellen: erst absichern, dann erweitern',{placeholder:'title'});
s.addShape(pres.shapes.LINE,{x:1.0,y:2.35,w:11.3,h:0,line:{color:HX.teal,width:3}});
const wv=[['1','Nov–Dez 2026','Team-Account + KI-Regel · Skill absichern (E6, E7) · Auslastung je MA entfernen'],['2','Jan–Feb 2027','Vertretung einweisen · Chef-Übersicht (E5)'],['3','ab März 2027','Sprachnotiz testen (E3), dann entscheiden']];
wv.forEach((w,i)=>{const x=0.8+i*4.1;circ(s,x+1.6,2.0,0.7,HX.navy,w[0]);card(s,x,3.0,3.9,2.3,C.background2);
 tb(s,w[1],{x:x+0.25,y:3.15,w:3.4,h:0.45,fontSize:18,bold:true,color:C.text2});tb(s,w[2],{x:x+0.25,y:3.65,w:3.4,h:1.5,valign:'top'});});
tb(s,[{text:'Erfolgskriterium Welle 1: ',options:{bold:true}},{text:'drei Berichte in Folge ohne Abweichung in den Vormonaten, Freigabe ≤ 15 Minuten.'}],{x:0.8,y:5.7,w:11.7,h:0.6,color:C.text2});

// 8 Empfehlung
pres.addSection({title:'Empfehlung'});
s=add('DARK','Empfehlung');
s.addText('Jetzt geht es um Vertrauen in die Zahlen',{placeholder:'title'});
s.addText([{text:'1  Claude-Team-Account einrichten (AVV)',options:{breakLine:true}},{text:'2  Skill im Dezember mit Claude Code absichern',options:{breakLine:true}},{text:'3  Nächster Schritt: Entscheidung der GF bis 30.11.2026',options:{bold:true,color:C.background1}}],{placeholder:'body'});

(async()=>{const f=process.argv[2];await pres.writeFile({fileName:f});await applyTheme(f,THEME);})();
