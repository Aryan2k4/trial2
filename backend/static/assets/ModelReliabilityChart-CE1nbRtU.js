import{j as e}from"./vendor-motion-G1kbuJbr.js";import{R as C,S as D,C as R,X as S,Y as E,Z as L,T as A,b as T,c as z}from"./vendor-charts-DYwLCEaI.js";const B={high:{label:"RELIABLE",color:"#2DD4BF"},medium:{label:"MODERATE",color:"#f0a860"},low:{label:"LOW CONFIDENCE",color:"#ef4444"}};function F(a){return a>=.7?"high":a>=.4?"medium":"low"}function I({active:a,payload:r,unit:t}){if(!a||!(r!=null&&r.length))return null;const{actualDisplay:i,predictedDisplay:s,lower:o,upper:c}=r[0].payload;return e.jsxs("div",{className:`
    bg-slate-900/95
    border
    border-slate-700
    rounded-lg
    px-3
    py-2
    font-mono
    text-[11px]
    text-white
    shadow-xl
    `,children:[e.jsxs("div",{children:["actual:"," ",i," ",t]}),e.jsxs("div",{children:["predicted:"," ",s," ",t]}),o!=null&&c!=null&&e.jsxs("div",{className:"text-slate-400",children:["80% interval: ",o,"–",c," ",t]})]})}function X({title:a,subtitle:r,data:t,unit:i=""}){var y;if(!((y=t==null?void 0:t.points)!=null&&y.length))return e.jsx("div",{className:`
      bg-paper-raised
      dark:bg-panel
      border
      border-slate-200
      dark:border-slate-800
      rounded-xl
      p-5
      text-sm
      text-slate-500
      `,children:"No model prediction data available yet."});const{points:s,r2:o,model:c}=t,v=F(o),d=B[v],u=s.every(n=>n.lower!=null&&n.upper!=null),f=s.flatMap(n=>u?[n.actual,n.predicted,n.lower,n.upper]:[n.actual,n.predicted]),p=Math.min(...f),x=Math.max(...f),b=(x-p)*.08||1,l=[Math.floor(p-b),Math.ceil(x+b)],g=Math.max(...s.map(n=>n.actual)),j=(x-p)*.012||.4;let m=0;const k=s.map(n=>{const h=Math.abs(n.actual-g)<1e-6,N=h&&Math.abs(n.predicted-g)<2,w=h?(m%9-4)*j:0,M=N?((m+3)%7-3)*j:0;return h&&(m+=1),{...n,actualDisplay:n.actual,predictedDisplay:n.predicted,actual:n.actual+w,predicted:n.predicted+M}});return e.jsxs("div",{className:`
    bg-paper-raised
    dark:bg-panel

    border
    border-slate-200
    dark:border-slate-800

    rounded-xl

    p-5

    relative
    overflow-hidden

    hover:border-teal-500/30

    hover:shadow-lg

    transition-all

    duration-300

    `,children:[e.jsxs("div",{className:`
      flex
      items-center
      justify-between
      mb-2
      gap-3
      flex-wrap
      `,children:[e.jsxs("div",{className:`
        flex
        items-center
        gap-2
        `,children:[e.jsx("h3",{className:`
          font-display
          text-sm
          font-medium
          text-ink
          dark:text-slate-200
          tracking-wide
          `,children:a}),e.jsx("span",{className:`
          text-[9px]
          font-mono
          tracking-widest

          px-2
          py-0.5

          rounded-full

          bg-teal-500/10

          border
          border-teal-500/30

          text-teal-400
          `,children:"AI MODEL"})]}),e.jsxs("span",{className:`
        font-mono
        text-[10px]
        tracking-widest
        px-2
        py-1
        rounded
        `,style:{color:d.color,backgroundColor:`${d.color}20`},children:[d.label," · ","R² ",o]})]}),e.jsxs("p",{className:`
      text-[11px]
      text-slate-500
      mb-4
      `,children:[r," · model: ",e.jsx("span",{className:`
      font-mono
      `,children:c})]}),e.jsx(C,{width:"100%",height:300,children:e.jsxs(D,{margin:{top:10,right:20,bottom:10,left:5},children:[e.jsx(R,{strokeDasharray:"2 4",className:`
          stroke-slate-200
          dark:stroke-slate-800
          `}),e.jsx(S,{type:"number",dataKey:"actual",domain:l,tick:{fontSize:10,fontFamily:"JetBrains Mono"},className:`
          fill-slate-400
          `,label:{value:`actual (${i})`,position:"insideBottom",offset:-5,fontSize:10,fill:"#94a3b8"}}),e.jsx(E,{type:"number",dataKey:"predicted",domain:l,tick:{fontSize:10,fontFamily:"JetBrains Mono"},className:`
          fill-slate-400
          `,label:{value:`predicted (${i})`,angle:-90,position:"insideLeft",fontSize:10,fill:"#94a3b8"}}),e.jsx(L,{range:[35,35]}),e.jsx(A,{content:e.jsx(I,{unit:i}),cursor:{strokeDasharray:"3 3"}}),e.jsx(T,{segment:[{x:l[0],y:l[0]},{x:l[1],y:l[1]}],stroke:"#94a3b8",strokeDasharray:"5 5",strokeWidth:1.5,label:{value:"perfect prediction",position:"insideTopRight",fontSize:9,fill:"#94a3b8"}}),e.jsx(z,{data:k,fill:d.color,fillOpacity:.55,r:4})]})}),e.jsxs("div",{className:`
      mt-3
      text-[11px]
      font-mono
      text-slate-500
      leading-relaxed
      `,children:["● Points close to diagonal = accurate prediction",e.jsx("br",{}),"● Scattered points = higher prediction error",e.jsx("br",{}),"● Cluster near the top-right = healthy engines correctly predicted near the RUL ceiling (spread slightly apart so overlapping points stay visible)",u&&e.jsxs(e.Fragment,{children:[e.jsx("br",{}),"● Hover any point for its 80% prediction interval (p10–p90)"]})]})]})}export{X as M};
