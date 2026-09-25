import { useState } from 'react';

export default function SumCalc() { 
    const [num1, setNum1] = useState(0);
    const [num2, setNum2] = useState(0);
    const [result, setResult] = useState(0);

    return (
    <>
      <p>Number 1: <input type="text" 
      value={num1} onChange={(e) => {setNum1(parseInt(e.target.value) || 0);}}/></p>
      <p>Number 2: <input type="text" 
      value={num2} onChange={(e) => {setNum2(parseInt(e.target.value) || 0);}}/></p>
      <p> <button onClick={ () => {setResult(num1 + num2);}}>Calculate Sum </button> </p>
      <p>Sum of {num1} and {num2} : {result}</p>

    </>
     
    )
}
