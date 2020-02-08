import React from 'react';
import BpkText from 'bpk-component-text';
import BpkPanel from 'bpk-component-panel';

import STYLES from './App.scss';

import Search from './Search';


const App = () => (
  <div className={STYLES['App']}>
    <header className={STYLES['App__header']}>
      <div className={STYLES['App__header-inner']}>
        <BpkText tagName="h1" textStyle="xxl" className={STYLES['App__heading']}>Concert Genie</BpkText>
      </div>
    </header>
    <main className={STYLES['App__main']}>
      <BpkPanel fullWidth={true}>
        Concert Genie allows you to predict what your favorite artist is going to play on their next live performance.
        Just search for whatever you feel like and we will generate a playlist for you!
      </BpkPanel>
      <Search/>
    </main>
  </div>
);

export default App;
