/* ==========================================================================
   Chamunda Cab - Fleet & Rate Card (single source of truth)
   Used by: fleet.html (all 10 vehicles), index.html (featured preview),
            booking.html (vehicle dropdown).

   >>> TO UPDATE PRICES: only edit the `rate` value of each vehicle below,
       using the per-km figure from your Rate Card, e.g.  rate: '11'
       or a range:  rate: '11 - 12'.   Leave '' to show "Call for rate".
       Rates below are from the official Rate Card (shown as \u20B9<rate>/km).
   ========================================================================== */
/* WhatsApp booking link used by every WhatsApp button on the site */
window.WA_LINK = 'https://wa.me/916352179909';

window.FLEET = [
  { id:'wagonr',   cat:'car',   type:'Hatchback',        name:'WagonR New', seats:'4 Seater', rate:'11', icon:'car-front',  img:'images/(1)WagonR New (Hatchback).png',
    desc:'Budget-friendly pick for solo travellers, couples, and short local or one-way trips.' },
  { id:'dzire',    cat:'car',   type:'Sedan',            name:'Swift Dzire', seats:'5 Seater', rate:'12', icon:'car-front',  img:'images/Swift-Dzire.png',
    desc:'Best for daily city rides, airport pickups, and small family one-way trips.' },
  { id:'ertiga',   cat:'suv',   type:'MUV',              name:'New Model Ertiga', seats:'7 Seater', rate:'14', icon:'car-front-fill', img:'images/New-Model-Ertiga.png',
    desc:'Family favourite for comfortable highway travel with extra legroom.' },
  { id:'carens',   cat:'suv',   type:'Premium MUV',      name:'Kia Carens', seats:'7 Seater', rate:'15', icon:'car-front-fill', img:'images/Kia-Carens.jpg',
    desc:'Spacious, modern cabin for family holidays and comfortable long-distance runs.' },
  { id:'tuv300',   cat:'suv',   type:'SUV',              name:'TUV 300 Plus', seats:'8 Seater', rate:'17', icon:'truck-front', img:'images/TUV-300-Plus.jpg',
    desc:'Rugged, roomy SUV for bigger families and groups on highway or village routes.' },
  { id:'innova',   cat:'suv',   type:'MUV',              name:'Innova', seats:'7 Seater', rate:'17', icon:'car-front-fill', img:'images/Innova.jpg',
    desc:'Reliable long-distance favourite for pilgrimage circuits and family tours.' },
  { id:'crysta',   cat:'suv',   type:'Premium SUV',      name:'Innova Crysta New Model', seats:'8 Seater', rate:'20', icon:'stars',      img:'images/Innova-Crysta.jpeg',
    desc:'Executive comfort for VIP guests, long pilgrimage circuits, and weddings.' },
  { id:'tt17',     cat:'coach', type:'Tempo Traveller',  name:'17 Seater Tempo Traveller', seats:'17 Seater', rate:'30', icon:'bus-front',  img:'images/17-Seater-Tempo-Traveller.jpg',
    desc:'Pushback seating for group tours, family functions, and corporate outings.' },
  { id:'tt20',     cat:'coach', type:'Tempo Traveller',  name:'20 Seater Tempo Traveller', seats:'20 Seater', rate:'35', icon:'bus-front',  img:'images/20-Seater-Tempo-Traveller.jpg',
    desc:'Extra capacity for school trips, baraat parties, and large yatra groups.' },
  { id:'urbania',  cat:'coach', type:'Luxury Van',       name:'New Luxury Urbania', seats:'16+1 Seater', rate:'35', icon:'stars',    img:'images/New-Luxury-Urbania.png',
    desc:'Premium luxury van for destination weddings, VIP groups, and executive travel.' }
];
window.fleetRate = function (v) { return v.rate ? '\u20B9' + v.rate + '/km' : 'Call for rate'; };
