let rate_btn = document.querySelector("#rate-btn");
let slider = document.querySelector('input[type="range"]');
let en_sentence = '';
let simple_sentence = '';
let jci = 0;

// User Rating und Daten zurueck an flask schicken
rate_btn.addEventListener("click", function(e) {
	if(en_sentence !== null && en_sentence !== '') {
		console.log(slider.value);
		console.log(jci);
		console.log(en_sentence);
		console.log(simple_sentence);
		let rating = slider.value;

		let pack = {en_sentence: en_sentence, simple_sentence: simple_sentence, jci: jci, rating: rating}

		fetch(`${window.origin}/result/prepwritedb`, {
			method: 'POST',
			credentials: 'include',
			body: JSON.stringify(pack),
			cache: 'no-cache',
			headers: new Headers({
				'content-type': 'application/json'
			}),
		})


	}
});

// Satz in simple English markieren
function markSentence(jcindex, pos) {
	let selected = document.querySelector('.simple-selection');
		if(selected){
			selected.className = ''
		}
	jci = jcindex;
	let element = document.querySelector('#sentence-'+pos);
	simple_sentence = element.textContent;
	if(jci > 0.2){
		element.classList.add('selected-10', 'simple-selection')
	} else {
		element.classList.add('selected-9', 'simple-selection')
	}

	element.scrollIntoView({ block: 'end',  behavior: 'smooth' });
}

// Satz per click auswaehlen und zurueck an flask schicken
document.querySelector(".en-text").addEventListener("click", function(e) {
    e.stopPropagation();
	if(!e.target.classList.contains('en-text')) {
		let selected = document.querySelector('.selected')
		if(selected){
			selected.classList.remove('selected');
		}
		e.target.classList.add("selected");
		let sentence = {
			selected_sentence: e.target.textContent
		}
		en_sentence = e.target.textContent;

		fetch(`${window.origin}/result/compare`, {
			method: 'POST',
			credentials: 'include',
			body: JSON.stringify(sentence),
			cache: 'no-cache',
			headers: new Headers({
				'content-type': 'application/json'
			}),
		})
			.then(res => res.json())
			.then(res => markSentence(res[0], res[1]))


	}
});

// Range slider visuell
let rangeValue = function(){
  let newValue = slider.value;
  let target = document.querySelector('.value');
  target.innerHTML = newValue;
}

slider.addEventListener("input", rangeValue);