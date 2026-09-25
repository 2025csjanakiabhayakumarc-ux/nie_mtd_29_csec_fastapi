import { useState } from 'react';

export default function Square() { 
    const [num, setNum] = useState(0);
    const [square, setSquare] = useState(0);

    return (
    <>
      <p>Number: <input type="text" 
      value={num} onChange={(e) => {setNum(parseInt(e.target.value) || 0);}}/></p>
      <p> <button onClick={ () => {setSquare(num * num);}}>Calculate Square </button> </p>
      <p>Square of {num} : {square}</p>

    </>
     
    )
}
