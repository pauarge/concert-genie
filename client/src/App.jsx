import React from 'react';
import BpkText from 'bpk-component-text';

import STYLES from './App.scss';

import Search from './Search';


export default () => (
  <div className={STYLES['App']}>
    <header className={STYLES['App__header']}>
      <div className={STYLES['App__header-inner']}>
        <BpkText tagName="h1" textStyle="xxl" className={STYLES['App__heading']}>Concert Genie</BpkText>
      </div>
    </header>
    <main className={STYLES['App__main']}>
      <Search/>
    </main>
  </div>
);
