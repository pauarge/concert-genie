import React from 'react';
import {BpkExtraLargeSpinner, SPINNER_TYPES} from "bpk-component-spinner";
import STYLES from "./Search.scss";


const Spinner = () => (
  <div>
    <br/>
    <p><BpkExtraLargeSpinner type={SPINNER_TYPES.primary}/></p>
    <p><i className={STYLES['grayedText']}>Loading results...</i></p>
  </div>
);

export default Spinner;
