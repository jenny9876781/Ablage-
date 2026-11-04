const sharp=require('sharp');const fs=require('fs');
const F='font-family="Liberation Sans, Arial, sans-serif"';
// Swimlane
const lanes=['GF / Berater','Assistenz','Partnerfirma'];
const steps=[ // lane, label, status: red/green/blue
 [0,'1 Termin\neintragen','red','S4'],[0,'2 Fahrt\nerfassen','green','gelöst'],[1,'3 Export','blue',''],[1,'4 Bericht\nerzeugen','red','S1'],
 [1,'5 Prüfen','red','S2'],[1,'6 Termine\nnachtragen','red','S4'],[1,'7 Zuordnung\npflegen','blue',''],[0,'8 Durchsicht\nFreigabe','red','S3'],[1,'9 Versand','blue',''],[2,'erhält\nBericht','grey','']];
const col={red:'#D9644A',green:'#3E8E5E',blue:'#2E6E8E',grey:'#8AA9BA'};
const W=1640,LH=170,X0=210,TOP=20,BW=138,BH=96,GAP=20;
let s=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${TOP+LH*3+70}" viewBox="0 0 ${W} ${TOP+LH*3+70}"><rect width="100%" height="100%" fill="#fff"/>`;
lanes.forEach((l,i)=>{const y=TOP+i*LH;s+=`<rect x="0" y="${y}" width="${W}" height="${LH}" fill="${i%2?'#F6F9FB':'#EEF3F6'}"/><text x="20" y="${y+LH/2+8}" ${F} font-size="24" font-weight="bold" fill="#1F3A4D">${l}</text>`;});
const pos=[];
steps.forEach((st,i)=>{const idx=i<9?i:8;const x=X0+idx*(BW+GAP)+(i===9?0:0);const y=TOP+st[0]*LH+(LH-BH)/2;pos.push([x,y]);});
pos[9]=[X0+8*(BW+GAP),TOP+2*LH+(LH-BH)/2];
// arrows
for(let i=0;i<9;i++){const [x1,y1]=pos[i],[x2,y2]=pos[i+1];const ax=x1+BW,ay=y1+BH/2;
 if(i===8){s+=`<line x1="${x1+BW/2}" y1="${y1+BH}" x2="${x2+BW/2}" y2="${y2-6}" stroke="#5B6B75" stroke-width="3" marker-end="url(#a)"/>`;continue;}
 s+=`<path d="M${ax} ${ay} L${ax+GAP/2} ${ay} L${ax+GAP/2} ${y2+BH/2} L${x2-4} ${y2+BH/2}" fill="none" stroke="#5B6B75" stroke-width="3" marker-end="url(#a)"/>`;}
s+=`<defs><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#5B6B75"/></marker></defs>`;
steps.forEach((st,i)=>{const [x,y]=pos[i];s+=`<rect x="${x}" y="${y}" width="${BW}" height="${BH}" rx="12" fill="${col[st[2]]}"/>`;
 st[1].split('\n').forEach((t,k)=>{s+=`<text x="${x+BW/2}" y="${y+34+k*26}" ${F} font-size="20" font-weight="bold" fill="#fff" text-anchor="middle">${t}</text>`;});
 if(st[3])s+=`<text x="${x+BW/2}" y="${y+BH-10}" ${F} font-size="16" fill="#fff" text-anchor="middle">${st[3]}</text>`;});
const ly=TOP+LH*3+40;
[['#D9644A','offene Schwachstelle'],['#3E8E5E','durch den Skill gelöst'],['#2E6E8E','unkritischer Schritt']].forEach((l,i)=>{const x=20+i*380;s+=`<rect x="${x}" y="${ly-20}" width="26" height="26" rx="5" fill="${l[0]}"/><text x="${x+38}" y="${ly}" ${F} font-size="22" fill="#1F3A4D">${l[1]}</text>`;});
s+='</svg>';
// Vorher/Nachher
let b=`<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="360"><rect width="100%" height="100%" fill="#fff"/>`;
const sc=820/16;
b+=`<text x="20" y="40" ${F} font-size="26" font-weight="bold" fill="#1F3A4D">Aufwand je Monatsbericht</text>`;
const bar=(y,lab,h,hmax,c,t)=>`<text x="20" y="${y+42}" ${F} font-size="24" fill="#1F3A4D">${lab}</text><rect x="300" y="${y}" width="${h*sc}" height="60" rx="8" fill="${c}"/>`+(hmax?`<rect x="${300+h*sc}" y="${y}" width="${(hmax-h)*sc}" height="60" rx="8" fill="${c}" opacity="0.35"/>`:'')+`<text x="${300+(hmax||h)*sc+16}" y="${y+42}" ${F} font-size="28" font-weight="bold" fill="${c}">${t}</text>`;
b+=bar(80,'früher von Hand',12,16,'#D9644A','12–16 h');
b+=bar(180,'heute mit Skill',2,0,'#3E8E5E','ca. 2 h');
b+=`<text x="300" y="300" ${F} font-size="20" fill="#5B6B75">heute: 1 h Bericht + ca. 1 h erneute Prüfung wegen Fehlern (entfällt nach der Skill-Absicherung)</text></svg>`;
(async()=>{await sharp(Buffer.from(s)).png().toFile('swimlane.png');await sharp(Buffer.from(b)).png().toFile('vorher_nachher.png');})();
