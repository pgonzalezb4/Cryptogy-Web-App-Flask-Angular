import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { CryptogyService } from '../services/cryptogy.service';

@Component({
  selector: 'app-classic',
  templateUrl: './classic.component.html',
  styleUrls: ['./classic.component.css']
})
export class ClassicComponent implements OnInit {

  randomKeyLoading: boolean = false;
  errorRandomKey: boolean = false;

  partitionError: boolean = false;

  encryptLoading: boolean = false;
  errorEncrypt: boolean = false;

  decryptLoading: boolean = false;
  errorDecrypt: boolean = false;

  analyzeLoading: boolean = false;
  errorAnalyze: boolean = false;
  errorAnalyzeMessage: string = "";

  imageLoading: boolean = false;
  errorImage: boolean = false;
  urlImage1: string | ArrayBuffer = null;
  urlImage2: string | ArrayBuffer = null;

  form: FormGroup;
  key: string = "";
  invalidKey: boolean = false;
  constructor(private cryptoService: CryptogyService) { }

  ngOnInit(): void {
    this.form = new FormGroup({
      cipher: new FormControl("permutation", { validators: Validators.required }),
      keyLength: new FormControl(5),
      key: new FormControl(null, { validators: Validators.required }),
      cleartext: new FormControl(''),
      ciphertext: new FormControl(''),
      keyStream: new FormControl(''), 
      numPartitions: new FormControl(2, {validators: Validators.required} )
    });
    this.generate_random_key();
  }

  cryptosystem_change() {
    this.generate_random_key();
    this.form.patchValue({"cleartext": ""});
    this.form.patchValue({"ciphertext": ""}); 
    this.form.updateValueAndValidity();
  }

  generate_random_key() {
    this.invalidKey = false;
    this.randomKeyLoading = true;
    this.errorRandomKey = false;
    let values = this.form.value;
    this.cryptoService.get_random_key(
      values.cipher,
      values.keyLength, 
      values.numPartitions
    )
      .subscribe(data => {
        console.log(data);
        this.form.patchValue({"key": data["random_key"] })
        this.form.updateValueAndValidity();
        this.randomKeyLoading = false;
      }, err => {
        console.log(err);
        if(err.error == "Invalid Key"){
          this.invalidKey = true;
        }
        this.errorRandomKey = true;
        this.randomKeyLoading = false;
      })
  }

  encrypt() {

    this.invalidKey = false;
    let values = this.form.value;
    this.encryptLoading = true;
    this.errorEncrypt = false;
    this.cryptoService.encrypt(
      values.key,
      values.cipher,
      values.cleartext, 
      values.keyLength, 
      values.numPartitions
    ).subscribe(
      data => {
        this.encryptLoading = false;
        this.form.patchValue({"ciphertext": data["ciphertext"] });
        this.form.updateValueAndValidity();
        if(data["key_stream"]){
          this.form.patchValue({"keyStream": data["key_stream"]});
          this.form.updateValueAndValidity();
        }
      }, err => {
        if(err.error == "Invalid Key"){
          this.invalidKey = true;
        }
        this.encryptLoading = false;
        this.errorEncrypt = true;
      }
    )
  }

  decrypt() {
    let values = this.form.value;
    this.decryptLoading = true;
    this.errorDecrypt = false;
    this.cryptoService.decrypt(
      values.key,
      values.cipher,
      values.ciphertext, 
      values.keyLength, 
      values.keyStream, 
      values.numPartitions
    ).subscribe(
      data => {
        this.decryptLoading = false;
        this.form.patchValue({"cleartext": data["cleartext"]});
        this.form.updateValueAndValidity();
      }, err => {
        this.decryptLoading = false;
        this.errorDecrypt = true;
      }
    )
  }

  clearText(){
    this.form.patchValue({"cleartext":""})
    this.form.updateValueAndValidity();
  }

  clearCipherText(){
    this.form.patchValue({"ciphertext":""})
    this.form.updateValueAndValidity();
  }

  analyze() { 
    let values = this.form.value;
    this.analyzeLoading = true;
    this.errorAnalyze = false;
    this.form.controls["keyStream"].enable();
    this.cryptoService.analize(
      values.cipher, 
      values.ciphertext, 
      values.cleartext,
      values.numPartitions
    ).subscribe(
      data => {
        this.analyzeLoading = false;
        this.form.patchValue({"cleartext": data["cleartext"]});
        this.form.updateValueAndValidity();
      }, 
      err => {
        this.errorAnalyzeMessage = err.error;
        this.errorAnalyze = true;
        this.analyzeLoading = false;
      }
    )
    this.form.controls["keyStream"].disable();
  }

  onFileSelected1(event: any){
    const files = event.target.files;
    if (files.length === 0)
        return;

    const mimeType = files[0].type;
    if (mimeType.match(/image\/*/) == null) {
        return;
    }

    const reader = new FileReader();
    reader.readAsDataURL(files[0]); 
    reader.onload = (_event) => { 
        this.urlImage1 = reader.result; 
    }
  }

  onFileSelected2(event: any){

  }
}
