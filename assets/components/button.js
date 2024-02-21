const buttonStyle = `
<style>

  .container{
    border:1px solid white;
  }

  button{
      width:100%;
      color:black;
      border:1px solid white;
      border-radius:0;
      padding:28px 27px 22px;
      text-align:left;
      display:flex;
      align-items:center;
      justify-content:space-between;
      position:relative;
      top:-5px;
      left:-5px;
      font-weight:500;
      background:white;
      font-family: "ITCF", sans-serif;
      font-weight: 600;
      font-size:15px;
      letter-spacing:2px;
      text-transform:uppercase;

  }
 
</style>
`;

const buttonHtml = ` 
  <div class="container">
   <button></button>
  </div>
`;

class Button extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = buttonStyle + buttonHtml;

    const text = this.getAttribute("text");
    const arrowColor = this.getAttribute("arrow-color");
    const background = this.getAttribute("background");

    const button = this.shadowRoot.querySelector("button");
    console.log(background);

    if (background) {
      button.style.backgroundColor = "#000";
      button.style.color = "#FFF";
    }

    button.innerHTML = ` ${text} <img src="../../assets/images/arrow.svg" alt="arrow" />`;
  }
}
customElements.define("button-component", Button);
