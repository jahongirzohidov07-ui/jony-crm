/* ENGLISH JOURNEY (2026-10-22) \u2014 diagnostik test natijasidagi yo'l xaritasi.
   placement.html (nomzod ekrani) va placement-report.html (hisobot) ikkalasi
   shu faylni ishlatadi: window.renderJourney(el, journey).
   Ma'lumot serverdan keladi (_pt_journey): bu yerda faqat chizish. */
(function () {
  if (window.renderJourney) return;
  var css = ''
    + '.ej{position:relative;overflow:hidden;border-radius:20px;padding:22px 18px 18px;margin:18px 0;text-align:left;'
    + 'background:radial-gradient(120% 90% at 100% 0%,#a78bfa 0%,#7c3aed 30%,#4f46e5 62%,#2563eb 100%);color:#fff;'
    + 'box-shadow:0 18px 40px rgba(79,70,229,.35);-webkit-print-color-adjust:exact;print-color-adjust:exact;'
    + 'font-family:-apple-system,"Segoe UI",Roboto,Inter,Arial,sans-serif}'
    + '.ej *{box-sizing:border-box}'
    + '.ej:before{content:"";position:absolute;right:-60px;top:-60px;width:200px;height:200px;border-radius:50%;'
    + 'background:radial-gradient(circle,rgba(250,204,21,.35),transparent 70%)}'
    + '.ej-k{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#c7d2fe;font-weight:700}'
    + '.ej-t{font-size:26px;font-weight:900;letter-spacing:-.02em;margin:2px 0 4px;line-height:1.1}'
    + '.ej-t span{background:linear-gradient(90deg,#fde047,#fb923c);-webkit-background-clip:text;background-clip:text;color:transparent}'
    + '.ej-s{font-size:13px;color:#ede9fe;margin:0 0 14px}'
    + '.ej-tg{display:flex;gap:6px;background:rgba(255,255,255,.16);border-radius:12px;padding:4px;margin-bottom:14px}'
    + '.ej-tg button{flex:1;border:0;border-radius:9px;padding:9px 6px;font-size:12.5px;font-weight:700;cursor:pointer;'
    + 'background:transparent;color:#c7d2fe;line-height:1.25}'
    + '.ej-tg button.on{background:#fff;color:#1e1b4b;box-shadow:0 4px 14px rgba(0,0,0,.25)}'
    + '.ej-tg small{display:block;font-weight:600;opacity:.75;font-size:10.5px}'
    + '.ej-hero{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}'
    + '.ej-h{border-radius:16px;padding:14px 12px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.3)}'
    + '.ej-h.gold{background:linear-gradient(150deg,rgba(250,204,21,.45),rgba(251,146,60,.3));border-color:#fde047}'
    + '.ej-h .b{font-size:12px;color:#e0e7ff;font-weight:700;letter-spacing:.04em}'
    + '.ej-h .n{font-size:40px;font-weight:900;line-height:1;margin:4px 0 6px;letter-spacing:-.03em}'
    + '.ej-h .d{font-size:15px;font-weight:800;color:#fde68a}'
    + '.ej-h .m{font-size:12px;color:#c7d2fe;margin-top:3px}'
    + '.ej-tl{position:relative;padding-left:4px}'
    + '.ej-r{position:relative;display:flex;gap:12px;padding:0 0 14px}'
    + '.ej-r:not(:last-child):after{content:"";position:absolute;left:21px;top:44px;bottom:0;width:2px;'
    + 'background:linear-gradient(#e9d5ff,rgba(233,213,255,.35))}'
    + '.ej-dot{flex:none;width:44px;height:44px;border-radius:50%;display:flex;flex-direction:column;align-items:center;'
    + 'justify-content:center;background:#4338ca;border:2px solid #c4b5fd;font-weight:900;font-size:14px;line-height:1}'
    + '.ej-dot small{font-size:8.5px;font-weight:700;color:#c7d2fe;margin-top:2px}'
    + '.ej-r.key .ej-dot{background:linear-gradient(150deg,#facc15,#f97316);border-color:#fde68a;color:#1e1b4b}'
    + '.ej-r.key .ej-dot small{color:#422006}'
    + '.ej-r.done .ej-dot{background:#065f46;border-color:#34d399}'
    + '.ej-c{flex:1;min-width:0;padding-top:2px}'
    + '.ej-c .h{display:flex;justify-content:space-between;gap:8px;align-items:baseline}'
    + '.ej-c .h b{font-size:15px}'
    + '.ej-c .h span{font-size:13px;font-weight:800;color:#fde68a;white-space:nowrap}'
    + '.ej-r.done .ej-c .h span{color:#6ee7b7}'
    + '.ej-ch{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}'
    + '.ej-ch i{font-style:normal;font-size:11.5px;font-weight:700;padding:4px 8px;border-radius:99px;'
    + 'background:rgba(255,255,255,.2);color:#fff;white-space:nowrap}'
    + '.ej-now{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:4px 0 12px}'
    + '.ej-now div{background:rgba(255,255,255,.16);border-radius:12px;padding:9px 8px;text-align:center}'
    + '.ej-now b{display:block;font-size:18px;font-weight:900}'
    + '.ej-now span{font-size:10.5px;color:#c7d2fe}'
    + '.ej-f{font-size:11px;color:#e0e7ff;line-height:1.5;margin:6px 0 0}'
    + '@media print{.ej-tg{display:none}.ej{break-inside:avoid}}';

  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function oy(m) { return m <= 0 ? 'hozir' : (m + ' oy'); }

  window.renderJourney = function (el, j, opts) {
    if (!el) return;
    if (!j || !j.milestones || !j.milestones.length) { el.innerHTML = ''; return; }
    if (!document.getElementById('ej-css')) {
      var st = document.createElement('style'); st.id = 'ej-css'; st.textContent = css;
      document.head.appendChild(st);
    }
    var pace = (opts && opts.pace) || el.getAttribute('data-pace') || 'std';
    var ms = j.milestones;
    var find = function (b) { for (var i = 0; i < ms.length; i++) if (ms[i].band === b) return ms[i]; return null; };
    var hero = ['6.0', '7.0'].map(function (b, i) {
      var m = find(b); if (!m) return '';
      var when = m.done ? 'Erishilgan \u2713' : m['date_' + pace];
      var sub = m.done ? 'darajangiz shundan yuqori'
        : (oy(m['months_' + pace]) + ' \u00b7 ' + fmt(m.lessons) + ' dars');
      return '<div class="ej-h' + (i === 0 ? ' gold' : '') + '"><div class="b">IELTS</div>'
        + '<div class="n">' + b + '</div><div class="d">' + when + '</div><div class="m">' + sub + '</div></div>';
    }).join('');
    var rows = ms.map(function (m) {
      var key = (m.band === '6.0' || m.band === '7.0') ? ' key' : '';
      var right = m.done ? '\u2713 bor' : m['date_' + pace];
      var chips = m.done
        ? '<i>\u2713 Bu darajadan o\'tgansiz</i>'
        : '<i>\u23f3 ' + oy(m['months_' + pace]) + '</i><i>\ud83d\udcda ' + fmt(m.lessons) + ' dars</i>'
          + '<i>\ud83d\udd24 +' + fmt(m.words_new) + ' so\'z (jami ' + fmt(m.words_total) + ')</i>'
          + (m.grammar_new > 0 ? '<i>\ud83e\udde9 +' + m.grammar_new + ' grammatika mavzusi</i>'
                               : '<i>\ud83c\udf93 akademik Writing/Speaking</i>');
      return '<div class="ej-r' + key + (m.done ? ' done' : '') + '"><div class="ej-dot">' + m.band
        + '<small>' + m.cefr + '</small></div><div class="ej-c"><div class="h"><b>IELTS ' + m.band
        + ' \u00b7 ' + m.cefr + '</b><span>' + right + '</span></div><div class="ej-ch">' + chips + '</div></div></div>';
    }).join('');
    el.innerHTML = '<div class="ej">'
      + '<div class="ej-k">English Journey</div>'
      + '<div class="ej-t">Sizning <span>IELTS</span> yo\'lingiz</div>'
      + '<p class="ej-s">Hozirgi darajangiz: ' + j.start.level + ' \u00b7 Unit ' + j.start.unit
      + '. Qachon qaysi ballga yetishingiz mumkin:</p>'
      + '<div class="ej-tg"><button type="button" data-p="std" class="' + (pace === 'std' ? 'on' : '') + '">Oddiy guruh'
      + '<small>oyiga ' + j.pace.std + ' dars</small></button><button type="button" data-p="int" class="'
      + (pace === 'int' ? 'on' : '') + '">\ud83d\udd25 Intensive<small>oyiga ' + j.pace.int + ' dars</small></button></div>'
      + '<div class="ej-hero">' + hero + '</div>'
      + '<div class="ej-now"><div><b>~' + fmt(j.words_now) + '</b><span>hozir bilgan so\'z</span></div>'
      + '<div><b>~' + j.grammar_now + '</b><span>o\'tilgan mavzu</span></div>'
      + '<div><b>411</b><span>jami grammatika</span></div></div>'
      + '<div class="ej-tl">' + rows + '</div>'
      + '<p class="ej-f">' + (j.disclaimer || '') + '<br>Asos: ' + (j.source || '') + '.</p>'
      + '</div>';
    var bs = el.querySelectorAll('.ej-tg button');
    for (var i = 0; i < bs.length; i++) {
      bs[i].onclick = function () {
        el.setAttribute('data-pace', this.getAttribute('data-p'));
        window.renderJourney(el, j);
      };
    }
  };
})();
