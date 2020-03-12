// Version 1.2.2 three-spritetext - https://github.com/vasturiano/three-spritetext
!function(t,e){"object"==typeof exports&&"undefined"!=typeof module?module.exports=e(require("three")):"function"==typeof define&&define.amd?define(["three"],e):(t=t||self).SpriteText=e(t.THREE)}(this,(function(t){"use strict";function e(t,e){if(!(t instanceof e))throw new TypeError("Cannot call a class as a function")}function n(t,e){for(var n=0;n<e.length;n++){var i=e[n];i.enumerable=i.enumerable||!1,i.configurable=!0,"value"in i&&(i.writable=!0),Object.defineProperty(t,i.key,i)}}function i(t){return(i=Object.setPrototypeOf?Object.getPrototypeOf:function(t){return t.__proto__||Object.getPrototypeOf(t)})(t)}function r(t,e){return(r=Object.setPrototypeOf||function(t,e){return t.__proto__=e,t})(t,e)}function o(t,e){return!e||"object"!=typeof e&&"function"!=typeof e?function(t){if(void 0===t)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return t}(t):e}function a(t){return function(t){if(Array.isArray(t)){for(var e=0,n=new Array(t.length);e<t.length;e++)n[e]=t[e];return n}}(t)||function(t){if(Symbol.iterator in Object(t)||"[object Arguments]"===Object.prototype.toString.call(t))return Array.from(t)}(t)||function(){throw new TypeError("Invalid attempt to spread non-iterable instance")}()}var c=window.THREE?window.THREE:{LinearFilter:t.LinearFilter,Sprite:t.Sprite,SpriteMaterial:t.SpriteMaterial,Texture:t.Texture};return function(t){function f(){var t,n=arguments.length>0&&void 0!==arguments[0]?arguments[0]:"",r=arguments.length>1&&void 0!==arguments[1]?arguments[1]:10,a=arguments.length>2&&void 0!==arguments[2]?arguments[2]:"rgba(255, 255, 255, 1)";return e(this,f),(t=o(this,i(f).call(this,new c.SpriteMaterial({map:new c.Texture}))))._text="".concat(n),t._textHeight=r,t._color=a,t._fontFace="Arial",t._fontSize=90,t._fontWeight="normal",t._canvas=document.createElement("canvas"),t._texture=t.material.map,t._texture.minFilter=c.LinearFilter,t._genCanvas(),t}var s,u,h;return function(t,e){if("function"!=typeof e&&null!==e)throw new TypeError("Super expression must either be null or a function");t.prototype=Object.create(e&&e.prototype,{constructor:{value:t,writable:!0,configurable:!0}}),e&&r(t,e)}(f,t),s=f,(u=[{key:"_genCanvas",value:function(){var t=this,e=this._canvas,n=e.getContext("2d"),i=this._text.split("\n"),r="".concat(this.fontWeight," ").concat(this.fontSize,"px ").concat(this.fontFace);n.font=r,e.width=Math.max.apply(Math,a(i.map((function(t){return n.measureText(t).width})))),e.height=this.fontSize*i.length,n.font=r,n.fillStyle=this.color,n.textBaseline="bottom",i.forEach((function(i,r){return n.fillText(i,(e.width-n.measureText(i).width)/2,(r+1)*t.fontSize)})),this._texture.image=e,this._texture.needsUpdate=!0;var o=this.textHeight*i.length;this.scale.set(o*e.width/e.height,o)}},{key:"clone",value:function(){return new this.constructor(this.text,this.textHeight,this.color).copy(this)}},{key:"copy",value:function(t){return c.Sprite.prototype.copy.call(this,t),this.color=t.color,this.fontFace=t.fontFace,this.fontSize=t.fontSize,this.fontWeight=t.fontWeight,this}},{key:"text",get:function(){return this._text},set:function(t){this._text=t,this._genCanvas()}},{key:"textHeight",get:function(){return this._textHeight},set:function(t){this._textHeight=t,this._genCanvas()}},{key:"color",get:function(){return this._color},set:function(t){this._color=t,this._genCanvas()}},{key:"fontFace",get:function(){return this._fontFace},set:function(t){this._fontFace=t,this._genCanvas()}},{key:"fontSize",get:function(){return this._fontSize},set:function(t){this._fontSize=t,this._genCanvas()}},{key:"fontWeight",get:function(){return this._fontWeight},set:function(t){this._fontWeight=t,this._genCanvas()}}])&&n(s.prototype,u),h&&n(s,h),f}(c.Sprite)}));