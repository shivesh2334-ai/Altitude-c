import {useMemo,useState} from 'react';
import {Activity,AlertTriangle,Check,ChevronRight,Download,HeartPulse,MapPin,Mountain,Navigation,Printer,Share2,ShieldAlert,Stethoscope} from 'lucide-react';
import {Analytics} from '@vercel/analytics/react';

type Risk='Minimal'|'Low'|'Moderate'|'High'|'Very High'|'Extreme';
type Symptom={id:string;label:string;group:'common'|'respiratory'|'danger'};
type LocationResult={id:string;name:string;latitude:number;longitude:number;elevation:number;type:string};
const symptoms:Symptom[]=[
 {id:'headache',label:'Headache',group:'common'},{id:'nausea',label:'Nausea or vomiting',group:'common'},{id:'fatigue',label:'Fatigue or weakness',group:'common'},{id:'dizziness',label:'Dizziness',group:'common'},{id:'anorexia',label:'Loss of appetite',group:'common'},
 {id:'dyspneaExertion',label:'Breathlessness on exertion',group:'respiratory'},{id:'dyspneaRest',label:'Breathlessness at rest',group:'respiratory'},{id:'dryCough',label:'Dry cough',group:'respiratory'},{id:'frothySputum',label:'Pink or frothy sputum',group:'danger'},{id:'chest',label:'Chest tightness or gurgling',group:'respiratory'},
 {id:'ataxia',label:'Loss of coordination',group:'danger'},{id:'confusion',label:'Confusion or altered consciousness',group:'danger'},{id:'lassitude',label:'Unable to self-care',group:'danger'},{id:'cyanosis',label:'Blue lips or fingertips',group:'danger'}];
const history=[['ams','Previous acute mountain sickness'],['hace','Previous HACE'],['hape','Previous HAPE'],['rapid','Ascent >500 m/day above 3,000 m'],['noAcclim','No intermediate acclimatization'],['activity','Immediate strenuous activity']];

function altitudeBand(m:number){
 if(m<1500)return{title:'Low altitude',risk:'Minimal' as Risk,oxygen:'>95%',note:'No altitude-related physiological changes expected.',tone:'safe'};
 if(m<2500)return{title:'Intermediate altitude',risk:'Low' as Risk,oxygen:'>90%',note:'Physiological changes may be detectable. Monitor new symptoms.',tone:'safe'};
 if(m<3500)return{title:'High altitude',risk:'Moderate' as Risk,oxygen:'85–90%',note:'Altitude illness is possible, especially after rapid ascent.',tone:'warn'};
 if(m<5800)return{title:'Very high altitude',risk:'High' as Risk,oxygen:'<90%',note:'Marked hypoxaemia may occur. Acclimatization is essential.',tone:'danger'};
 if(m<8000)return{title:'Extreme altitude',risk:'Very High' as Risk,oxygen:'<80%',note:'Marked hypoxaemia at rest; limit exposure and obtain expert support.',tone:'danger'};
 return{title:'Death zone',risk:'Extreme' as Risk,oxygen:'~55%',note:'Survival is time-limited. Expert support and oxygen are usually required.',tone:'danger'};
}

function makeAscentPlan(start:number,target:number){
 const rows:{day:number;altitude:number;action:string;note:string}[]=[]; let day=1; let current=start; let gains=0;
 if(target<=start)return[{day:1,altitude:start,action:'Review route',note:'Target altitude must be above the starting sleeping altitude.'}];
 if(start<1500&&target>2800){current=Math.min(2000,target);rows.push({day:day++,altitude:current,action:'Stage',note:'An intermediate overnight stop may reduce abrupt exposure.'});}
 if(current<3000&&target>3000){current=3000;rows.push({day:day++,altitude:current,action:'Reach base',note:'Monitor symptoms after the first substantial altitude exposure.'});}
 while(current<target&&rows.length<24){
  const gain=current>=3000?Math.min(450,target-current):Math.min(700,target-current); current+=gain; gains++;
  rows.push({day:day++,altitude:current,action:'Ascend',note:`Increase sleeping altitude by ${gain} m. Stop ascent if symptoms develop.`});
  if(current<target&&current>=3000&&gains%3===0)rows.push({day:day++,altitude:current,action:'Rest / acclimatize',note:'Sleep at the same altitude; an optional daytime climb should return lower to sleep.'});
 }
 return rows;
}

export default function App(){
 const [altitude,setAltitude]=useState(3500); const [startAltitude,setStartAltitude]=useState(1200); const [location,setLocation]=useState(''); const [checked,setChecked]=useState<Set<string>>(new Set()); const [profile,setProfile]=useState<Set<string>>(new Set()); const [tab,setTab]=useState<'plan'|'symptoms'>('plan');
 const [altitudeInput,setAltitudeInput]=useState('3500');
 const [locationResults,setLocationResults]=useState<LocationResult[]>([]); const [locationLoading,setLocationLoading]=useState(false); const [locationError,setLocationError]=useState('');
 const band=altitudeBand(altitude);
 const itinerary=useMemo(()=>makeAscentPlan(startAltitude,altitude),[startAltitude,altitude]);
 const toggle=(id:string,setter:React.Dispatch<React.SetStateAction<Set<string>>>)=>setter(old=>{const next=new Set(old);next.has(id)?next.delete(id):next.add(id);return next});
 const findLocation=async()=>{if(location.trim().length<2){setLocationError('Enter at least two characters.');return}setLocationLoading(true);setLocationError('');try{const response=await fetch(`/api/location?q=${encodeURIComponent(location.trim())}`);const payload=await response.json();if(!response.ok)throw new Error(payload.error||'Location lookup failed.');setLocationResults(payload.results||[])}catch(error){setLocationResults([]);setLocationError(error instanceof Error?error.message:'Location lookup failed.')}finally{setLocationLoading(false)}};
 const chooseLocation=(place:LocationResult)=>{const next=Math.min(8849,place.elevation);setLocation(place.name);setAltitude(next);setAltitudeInput(String(next));setLocationResults([]);setLocationError('')};
 const enterAltitude=()=>{const parsed=Math.round(Number(altitudeInput));if(!Number.isFinite(parsed)||parsed<0||parsed>8849){setLocationError('Enter an altitude between 0 and 8,849 metres.');return}setAltitude(parsed);setAltitudeInput(String(parsed));setLocationResults([]);setLocationError('')};
 const assessment=useMemo(()=>{
  const severe=['ataxia','confusion','lassitude','cyanosis','frothySputum','dyspneaRest'].some(x=>checked.has(x));
  const respiratory=['dyspneaExertion','dyspneaRest','dryCough','frothySputum','chest'].filter(x=>checked.has(x)).length;
  const lake=[checked.has('headache'),checked.has('nausea')||checked.has('anorexia'),checked.has('fatigue'),checked.has('dizziness')].filter(Boolean).length;
  let personal:Risk=band.risk; if(profile.has('hace')||profile.has('hape')||(altitude>=3500&&(profile.has('rapid')||profile.has('noAcclim'))))personal='High'; else if(profile.has('ams')||profile.has('rapid'))personal='Moderate';
  if(severe||respiratory>=2)return{level:'Emergency',tone:'danger',title:'Possible HACE or HAPE',text:'Stop ascent and descend immediately. Use oxygen if available and seek urgent medical/rescue assistance. Do not leave the person alone.',lake,personal};
  if(checked.has('headache')&&lake>=3)return{level:'Action required',tone:'warn',title:'Symptoms compatible with AMS',text:'Do not ascend further. Rest, hydrate normally, and reassess. Descend if symptoms worsen or fail to improve.',lake,personal};
  return{level:'Monitor',tone:'safe',title:checked.size?'Symptoms do not meet the screening threshold':'No symptoms selected',text:'Continue gradual ascent only if well. A symptom-free person can still develop altitude illness; reassess regularly.',lake,personal};
 },[altitude,band,checked,profile]);
 const reportText=()=>{const chosenFactors=history.filter(([id])=>profile.has(id)).map(([,label])=>label);const chosenSymptoms=symptoms.filter(item=>checked.has(item.id)).map(item=>item.label);return [`SAFE2PEAK ALTITUDE SAFETY SUMMARY`,`Generated: ${new Date().toLocaleString()}`,`Destination: ${location||'Not specified'}`,`Altitude: ${altitude.toLocaleString()} m (${Math.round(altitude*3.28084).toLocaleString()} ft)`,`Altitude category: ${band.title}`,`Altitude risk: ${band.risk}`,`Expected oxygen saturation: ${band.oxygen}`,`Personal risk: ${assessment.personal}`,`Assessment: ${assessment.level} — ${assessment.title}`,`Symptom screen: ${assessment.lake}/4`,`Risk factors: ${chosenFactors.length?chosenFactors.join('; '):'None selected'}`,`Symptoms: ${chosenSymptoms.length?chosenSymptoms.join('; '):'None selected'}`,`Recommendation: ${assessment.text}`,``,`SUGGESTED ASCENT SCHEDULE`,...itinerary.map(row=>`Day ${row.day}: ${row.action} — sleep at ${row.altitude.toLocaleString()} m. ${row.note}`),``,`IMPORTANT: Educational screening only; not a diagnosis. Do not ascend with worsening symptoms. Descend immediately and seek urgent help for confusion, loss of coordination, breathlessness at rest, blue lips/fingertips, or pink/frothy sputum.`].join('\n')};
 const downloadReport=()=>{const blob=new Blob([reportText()],{type:'text/plain;charset=utf-8'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`safe2peak-${(location||'altitude-report').replace(/[^a-z0-9]+/gi,'-').toLowerCase()}.txt`;link.click();URL.revokeObjectURL(url)};
 const shareWhatsApp=()=>{const compact=`SAFE2PEAK SUMMARY\n${location||'Destination'}: ${altitude.toLocaleString()} m\nRisk: ${assessment.personal} | ${assessment.level}\n${assessment.title}\n${assessment.text}\n\nEducational guidance only. Severe symptoms require immediate descent and urgent medical/rescue help.`;window.open(`https://wa.me/?text=${encodeURIComponent(compact)}`,'_blank','noopener,noreferrer')};
 const printReport=()=>{const report=reportText().replace(/[&<>]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[char]||char));const popup=window.open('','_blank');if(!popup)return;popup.opener=null;popup.document.write(`<!doctype html><html><head><title>Safe2Peak Summary</title><style>body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;padding:0 24px;color:#17221e}h1{color:#315e21}pre{white-space:pre-wrap;font:14px/1.55 Arial,sans-serif}.note{border-top:2px solid #315e21;margin-top:24px;padding-top:12px;color:#555}@media print{body{margin:0}}</style></head><body><h1>Safe2Peak</h1><pre>${report}</pre><p class="note">Altitude safety decision support • Easy My Care</p><script>window.onload=()=>window.print()<\/script></body></html>`);popup.document.close()};
 return <div className="app">
  <header><a className="brand" href="#top"><span><Mountain/></span><b>SAFE2PEAK</b></a><div className="medical"><HeartPulse/> Clinical altitude safety</div></header>
  <main id="top">
   <section className="hero"><div><p className="eyebrow">PLAN • RECOGNISE • DESCEND</p><h1>Climb informed.<br/><em>Return safely.</em></h1><p className="lead">A structured altitude-risk and symptom-screening companion based on established mountain-medicine principles.</p></div><div className="hero-mark"><Mountain/><span>{altitude.toLocaleString()} m</span></div></section>
   <div className="notice"><ShieldAlert/><div><b>Emergency rule</b><span>Confusion, loss of coordination, breathlessness at rest or pink frothy sputum: descend now and seek emergency help.</span></div></div>
   <nav className="tabs" aria-label="Assessment sections"><button className={tab==='plan'?'active':''} onClick={()=>setTab('plan')}><Navigation/> Trip risk</button><button className={tab==='symptoms'?'active':''} onClick={()=>setTab('symptoms')}><Stethoscope/> Symptoms</button></nav>
   <div className="dashboard">
    <section className="panel controls">
     <div className="panel-title"><div><p className="eyebrow">01 • DESTINATION</p><h2>Altitude profile</h2></div><MapPin/></div>
     <label>Destination name <div className="location-search"><input value={location} onChange={e=>setLocation(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')findLocation()}} placeholder="e.g. Leh, Kedarnath, Kilimanjaro"/><button type="button" onClick={findLocation} disabled={locationLoading}>{locationLoading?'Searching…':'Find altitude'}</button></div></label>
     {locationError&&<p className="location-error">{locationError}</p>}
     {locationResults.length>0&&<div className="location-results">{locationResults.map(place=><button type="button" key={place.id} onClick={()=>chooseLocation(place)}><MapPin/><span>{place.name}<small>{place.elevation.toLocaleString()} m • {place.latitude.toFixed(3)}, {place.longitude.toFixed(3)}</small></span><ChevronRight/></button>)}<p>Location © OpenStreetMap contributors • Elevation © Open-Meteo</p></div>}
     <label>Sleeping / destination altitude <output>{altitude.toLocaleString()} m <small>{Math.round(altitude*3.28084).toLocaleString()} ft</small></output><div className="altitude-entry"><input aria-label="Enter altitude in metres" type="number" inputMode="numeric" min="0" max="8849" step="1" value={altitudeInput} onChange={e=>setAltitudeInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')enterAltitude()}}/><button type="button" onClick={enterAltitude}>Enter altitude</button></div><input aria-label="Altitude slider in metres" type="range" min="0" max="8849" step="50" value={altitude} onChange={e=>{const next=Number(e.target.value);setAltitude(next);setAltitudeInput(String(next))}}/><div className="range-labels"><span>Sea level</span><span>8,849 m</span></div></label>
     <div className="band-card" data-tone={band.tone}><div><small>ALTITUDE CATEGORY</small><h3>{band.title}</h3></div><strong>{band.risk}</strong><p>{band.note}</p><span>Typical SpO₂ range: <b>{band.oxygen}</b></span></div>
     <p className="field-title">Personal and ascent risk factors</p><div className="checks">{history.map(([id,label])=><button key={id} onClick={()=>toggle(id,setProfile)} className={profile.has(id)?'selected':''}><i>{profile.has(id)&&<Check/>}</i><span>{label}</span></button>)}</div>
    </section>
    <section className="panel assessment">
     <div className="panel-title"><div><p className="eyebrow">02 • SCREENING</p><h2>Current symptoms</h2></div><Activity/></div>
     {(['common','respiratory','danger'] as const).map(group=><div className="symptom-group" key={group}><h3>{group==='common'?'Common AMS symptoms':group==='respiratory'?'Breathing symptoms':'Danger signs'}</h3><div className="checks">{symptoms.filter(s=>s.group===group).map(s=><button key={s.id} onClick={()=>toggle(s.id,setChecked)} className={(checked.has(s.id)?'selected ':'')+(group==='danger'?'red':'')}><i>{checked.has(s.id)&&<Check/>}</i><span>{s.label}</span></button>)}</div></div>)}
    </section>
    <aside className="panel result" data-tone={assessment.tone}>
     <p className="eyebrow">YOUR ASSESSMENT</p><div className="status-icon">{assessment.tone==='danger'?<AlertTriangle/>:<ShieldAlert/>}</div><span className="status">{assessment.level}</span><h2>{assessment.title}</h2><p>{assessment.text}</p>
     <dl><div><dt>Altitude risk</dt><dd>{band.risk}</dd></div><div><dt>Personal risk</dt><dd>{assessment.personal}</dd></div><div><dt>Symptom score*</dt><dd>{assessment.lake}/4</dd></div></dl>
     <div className="actions"><h3>Safer-ascent essentials</h3><p><ChevronRight/> Above 3,000 m, increase sleeping altitude by roughly 300–500 m/day.</p><p><ChevronRight/> Add a rest day every 3–4 days or after each 1,000 m gained.</p><p><ChevronRight/> Never ascend with worsening altitude symptoms.</p><p><ChevronRight/> Descent is the definitive response to severe illness.</p></div>
     <div className="report-actions"><button type="button" onClick={downloadReport}><Download/> Download</button><button type="button" onClick={shareWhatsApp}><Share2/> WhatsApp</button><button type="button" onClick={printReport}><Printer/> Print / PDF</button></div>
    </aside>
   </div>
   <section className="planner panel">
    <div className="planner-head"><div><p className="eyebrow">03 • ACCLIMATIZATION</p><h2>Day-by-day ascent planner</h2><p>Creates a conservative sleeping-altitude schedule. Terrain, transport, fitness and rescue access still require local expert planning.</p></div><Navigation/></div>
    <div className="planner-inputs"><label>Starting sleeping altitude <output>{startAltitude.toLocaleString()} m</output><input aria-label="Starting altitude" type="range" min="0" max={Math.max(altitude-100,100)} step="50" value={Math.min(startAltitude,Math.max(altitude-100,100))} onChange={e=>setStartAltitude(Number(e.target.value))}/></label><div className="plan-summary"><small>ESTIMATED MINIMUM</small><strong>{itinerary.length} days</strong><span>to reach {altitude.toLocaleString()} m</span></div></div>
    <div className="timeline">{itinerary.map(row=><article key={`${row.day}-${row.action}`} className={row.action.startsWith('Rest')?'rest':''}><b>{row.day}</b><div><small>DAY {row.day} • {row.action.toUpperCase()}</small><h3>{row.altitude.toLocaleString()} m</h3><p>{row.note}</p></div></article>)}</div>
   </section>
   <section className="prevention-grid">
    <article className="panel"><p className="eyebrow">PREVENTION PLAN</p><h2>Before departure</h2><ul><li>Build extra acclimatization days into fixed itineraries.</li><li>Arrange travel insurance, evacuation contacts and communication backup.</li><li>Discuss prior AMS, HACE/HAPE, cardiac or pulmonary disease with a clinician.</li><li>Carry prescribed medication only after reviewing contraindications, interactions and indication.</li></ul></article>
    <article className="panel medication"><p className="eyebrow">MEDICATION SAFETY</p><h2>Clinician-supervised options</h2><p>Acetazolamide is commonly considered for moderate/high-risk ascent. Dexamethasone is generally an alternative or emergency medication—not a substitute for acclimatization. Prior HAPE requires specialist planning; nifedipine or other agents are not for self-starting.</p><div className="mini-alert"><AlertTriangle/> Never use medication to continue ascending with worsening symptoms.</div></article>
    <article className="panel"><p className="eyebrow">FIELD CHECK</p><h2>Three non-negotiables</h2><ol><li>Do not ascend while symptomatic.</li><li>Descend for severe or worsening illness.</li><li>Never leave an unwell climber alone.</li></ol></article>
   </section>
   <section className="disclaimer"><b>Important medical disclaimer</b><p>This tool supports education and structured screening; it does not diagnose illness or replace a clinician, expedition doctor, trained guide, local rescue service, pulse oximetry, or an emergency plan. Symptoms and clinical deterioration matter more than a score. *The displayed four-domain screen is simplified and is not a substitute for a formal Lake Louise assessment.</p></section>
  </main><footer><div className="brand"><span><Mountain/></span><b>SAFE2PEAK</b></div><p>Altitude safety decision support • Easy My Care</p><p>© {new Date().getFullYear()}</p></footer>
  <Analytics />
 </div>;
}
