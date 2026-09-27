module.exports=new Proxy({}, {get:(_,k)=>k==="__esModule"?false:String(k)});
