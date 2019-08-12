let rate_btn = document.querySelector("#rate-btn");
let slider = document.querySelector('input[type="range"]');
let en_sentence = '';
let simple_sentence = '';
let jci = null;
let cosinevecindex = null;
let ltfidf = null;
let algorithm = '';
let user_selection = false;

// User Rating und Daten zurueck an flask schicken
rate_btn.addEventListener("click", function(e) {
	if(en_sentence !== null && en_sentence !== '') {
		let rating = slider.value;

		let alg_dd = document.querySelector('#curr-alg');
		algorithm = alg_dd.value;
		console.log("ALG: " + algorithm);

		let selected_simple = document.querySelectorAll('.simple-selection');
		simple_sentence = '';
		for(var i = 0; i <= selected_simple.length-1; i++){
			simple_sentence = simple_sentence + ' ' + selected_simple[i].textContent;
		}

		console.log("THIS:" + simple_sentence);
		if (user_selection == true){
			jci = -1;
			cosinevecindex = -1;
			ltfidf = -1;
		}

		let pack = {alg: algorithm, en_sentence: en_sentence, simple_sentence: simple_sentence, rating: rating, jci: jci, cosinevecindex: cosinevecindex, ltfidf:ltfidf}
		console.log(pack)
		fetch(`${window.origin}/result/prepwritedb`, {
			method: 'POST',
			credentials: 'include',
			body: JSON.stringify(pack),
			cache: 'no-cache',
			headers: new Headers({
				'content-type': 'application/json'
			}),
		})

		let selected = document.querySelectorAll(".simple-selection");

		for (var i = 0; i < selected.length; i++) {
   			selected[i].classList.remove('simple-selection', 'selected-10', 'selected-9');
		}

		selected = document.querySelector('.selected');
		if(selected){
			selected.classList.remove('selected');
		}


		while (selected.nextElementSibling.tagName.toLowerCase() != 'span'){
			selected = selected.nextElementSibling
		}

		selected = selected.nextElementSibling
		selected.classList.add("selected");

		alg_dd = document.querySelector('#curr-alg');
		console.log(alg_dd.value);
		let sentence = {
			selected_sentence: selected.textContent,
			selected_alg: alg_dd.value
		}
		en_sentence = selected.textContent;
		let loader = document.getElementById("loader");
  		loader.style.display = "block";

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
			.then(res => markSentence(res[0], res[1], res[2], res[3]))

	}
});


// Satz in simple English markieren
function markSentence(score, pos, sentence_quan, alg) {
	console.log(pos);
	let loader = document.getElementById("loader");
  	loader.style.display = "none";

	console.log("in")
	user_selection = false;

	let element = document.querySelector('#sentence-'+pos);
	for (var j = 0; j < sentence_quan; j++){

		console.log("markiert")
		element = document.querySelector('#sentence-'+(pos+j));

		if (element == null){
			console.log("isnull")
			continue;
		}

		if(alg.toString() == 'cosinevector'){
			cosinevecindex = score;

			if(cosinevecindex >= 0.84) {
			element.classList.add('selected-10', 'simple-selection');
			} else {
				if (typeof(element) != 'undefined' && element != null){
					element.classList.add('selected-9', 'simple-selection')
				}
			}
		}

		if(alg.toString() == 'jci'){
			jci = score;
			if(jci >= 0.21) {
			element.classList.add('selected-10', 'simple-selection');
			} else {
				if (typeof(element) != 'undefined' && element != null){
					element.classList.add('selected-9', 'simple-selection')
				}
			}
		}

		if(alg.toString() == 'ltfidf'){
			ltfidf = score;
			if(ltfidf >= 0.28) {
			element.classList.add('selected-10', 'simple-selection');
			} else {
				if (typeof(element) != 'undefined' && element != null){
					element.classList.add('selected-9', 'simple-selection')
				}
			}
		}
	}


	console.log("this is textc: " + simple_sentence)



	element.scrollIntoView({ block: 'end',  behavior: 'smooth' });
}

// Satz per click auswaehlen und zurueck an flask schicken
document.querySelector(".en-text").addEventListener("click", function(e) {
    e.stopPropagation();
    let selected = document.querySelectorAll(".simple-selection");

	for (var i = 0; i < selected.length; i++) {
   		selected[i].classList.remove('simple-selection', 'selected-10', 'selected-9');
	}
	if(!e.target.classList.contains('en-text')) {
		let selected = document.querySelector('.selected')
		if(selected){
			selected.classList.remove('selected');
		}
		e.target.classList.add("selected");
		let alg_dd = document.querySelector('#curr-alg');
		console.log(alg_dd.value);
		let sentence = {
			selected_sentence: e.target.textContent,
			selected_alg: alg_dd.value
		}
		en_sentence = e.target.textContent;
		let loader = document.getElementById("loader");
  		loader.style.display = "block";
		console.log(sentence)
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
			.then(res => markSentence(res[0], res[1], res[2], res[3]))


	}
});

// Range slider visuell
let rangeValue = function(){
  let newValue = slider.value;
  let target = document.querySelector('.value');
  target.innerHTML = newValue;
};

slider.addEventListener("input", rangeValue);

// Custom auswahl
document.querySelector(".simple-text").addEventListener("click", function(e) {
	user_selection = true;
    e.stopPropagation();

    if(!e.target.classList.contains('simple-text')) {
		e.target.classList.toggle("simple-selection");
		if(e.target.classList.contains('selected-9')){
			e.target.classList.remove('selected-9');
		}
		if(e.target.classList.contains('selected-10')){
			e.target.classList.remove('selected-10')
		}
	}
})