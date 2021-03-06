import React from 'react';
import BpkButton from 'bpk-component-button';
import {colors} from 'bpk-tokens/tokens/base.es6';
import {withButtonAlignment} from "bpk-component-icon";
import LongArrowRightIconSm from "bpk-component-icon/sm/long-arrow-right";
import BpkSectionList from "bpk-component-section-list";
import BpkSectionListSection from "bpk-component-section-list/src/BpkSectionListSection";
import BpkSectionListItem from "bpk-component-section-list/src/BpkSectionListItem";
import BpkAutosuggestSuggestion from "bpk-component-autosuggest/src/BpkAutosuggestSuggestion";
import BpkAutosuggest from "bpk-component-autosuggest/src/BpkAutosuggest";
import BpkBannerAlert, {ALERT_TYPES} from 'bpk-component-banner-alert';
import BpkImage from "bpk-component-image";
import Spinner from "./Spinner";
import BpkGridContainer from "bpk-component-grid/src/BpkGridContainer";
import BpkGridRow from "bpk-component-grid/src/BpkGridRow";
import BpkGridColumn from "bpk-component-grid/src/BpkGridColumn";
import BpkList from "bpk-component-list/src/BpkList";
import BpkListItem from "bpk-component-list/src/BpkListItem";
import BpkPanel from "bpk-component-panel";

import STYLES from './Search.scss';

const DONE_INTERVAL = 200;
// const BASE_URL = 'https://concert-genie.herokuapp.com';
const BASE_URL = 'http://127.0.0.1:5000';

const AlignedArrow = withButtonAlignment(LongArrowRightIconSm);

const getSuggestionValue = item => item;

const renderSuggestion = suggestion => (
  <BpkAutosuggestSuggestion
    value={suggestion}
    indent={suggestion.indent}
  />
);

class Search extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      value: '',
      suggestions: [],
      typingTimer: null,
      results: [],
      artistImg: null,
      uris: [],
      showSpinner: false,
      spotifyLink: null,
      artist: '',
      errored: false,
      stats: {}
    };

    this.clearSearch = this.clearSearch.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.exportSpotify = this.exportSpotify.bind(this);
  }

  clearSearch() {
    this.setState({
      value: '',
      suggestions: [],
      typingTimer: null,
      results: [],
      artistImg: null,
      uris: [],
      showSpinner: false,
      spotifyLink: null,
      errored: false,
      stats: {},
      artist: ''
    });
  }

  getSuggestions(val) {
    if (this.state.value.length > 1) {
      fetch(`${BASE_URL}/suggest?artist=${val.trim()}`)
        .then(res => res.json())
        .then(
          result => this.setState({
            suggestions: result,
          }),
          error => console.log(error)
        )
    }
  }

  handleSubmit(event) {
    event.preventDefault();
    this.setState({
      results: [],
      showSpinner: true,
    }, () => {
      fetch(`${BASE_URL}/?artist=${this.state.value}`)
        .then(res => res.json())
        .then(
          result => this.setState({
            results: result['playlist'],
            artistImg: result['img'],
            stats: result['stats'],
            uris: result['uris'],
            showSpinner: false,
            errored: false,
            spotifyLink: null,
            artist: this.state.value
          }),
          error => {
            console.log(error);
            this.setState({
              errored: true,
              showSpinner: false
            })
          }
        )
    })
  }

  onChange = (e, {newValue}) => {
    this.setState({
      value: newValue,
    });
  };

  onSuggestionsFetchRequested = ({value}) => {
    clearTimeout(this.state.typingTimer);
    this.setState({
      typingTimer: setTimeout(() => this.getSuggestions(value), DONE_INTERVAL)
    });
  };

  onSuggestionsClearRequested = () => {
    this.setState({
      suggestions: [],
    });
  };

  exportSpotify = () => {
    fetch(`${BASE_URL}/create-playlist?artist=${this.state.artist}&uris=${this.state.uris}`)
      .then(res => res.json())
      .then(
        result => this.setState({
          spotifyLink: result
        }),
        error => console.log(error),
      )
  };

  render() {
    const {value, suggestions} = this.state;

    const inputProps = {
      id: 'my-autosuggest',
      name: 'my-autosuggest',
      placeholder: 'Start by typing an artist name...',
      value,
      onChange: this.onChange,
    };

    return (
      <>
        <BpkGridContainer>
          <BpkGridRow>
            <BpkGridColumn width={8} offset={2} tabletWidth={12} tabletOffset={0}>
              <BpkPanel className={STYLES['customPanel']} fullWidth={true}>
                Concert Genie allows you to predict what your favorite artist is going to play on their next live
                performance.
                Just search for whatever you feel like and we will generate a playlist for you!
              </BpkPanel>
              <form onSubmit={this.handleSubmit}>
                <p>
                  <BpkAutosuggest
                    suggestions={suggestions}
                    onSuggestionsFetchRequested={this.onSuggestionsFetchRequested}
                    onSuggestionsClearRequested={this.onSuggestionsClearRequested}
                    getSuggestionValue={getSuggestionValue}
                    renderSuggestion={renderSuggestion}
                    inputProps={inputProps}
                  />
                </p>
                <p>
                  <BpkButton onClick={this.clearSearch} destructive={true}>
                    Clear
                  </BpkButton>
                  &nbsp;
                  <BpkButton submit={true}>
                    Search&nbsp;
                    <AlignedArrow fill={colors.colorWhite}/>
                  </BpkButton>
                </p>
              </form>
            </BpkGridColumn>
          </BpkGridRow>
        </BpkGridContainer>
        {this.state.errored &&
        <BpkBannerAlert
          message="Could not generate a playlist for the artist."
          type={ALERT_TYPES.ERROR}
        />
        }
        {this.state.showSpinner && <Spinner/>}
        {this.state.results.length > 0 &&
        <div>
          <BpkGridContainer>
            <BpkGridRow>
              <BpkGridColumn width={4} mobileWidth={12}>
                <h2>{this.state.artist}</h2>
                <h3>Artist stats</h3>
              </BpkGridColumn>
              <BpkGridColumn width={4} mobileWidth={12}>
                <p>Usually starts with <b>{this.state.stats.first_song}</b>.</p>
                <p>Usually ends with <b>{this.state.stats.last_song}</b>.</p>
              </BpkGridColumn>
              <BpkGridColumn width={4} mobileWidth={12}>
                <b>Top songs</b>:
                <BpkList ordered>
                  <BpkListItem>{this.state.stats.top_three[0]}</BpkListItem>
                  <BpkListItem>{this.state.stats.top_three[1]}</BpkListItem>
                  <BpkListItem>{this.state.stats.top_three[2]}</BpkListItem>
                </BpkList>
              </BpkGridColumn>
            </BpkGridRow>
            <BpkGridRow>
              <BpkGridColumn width={7} tabletWidth={12}>
                <p>
                  <BpkImage
                    altText="plot"
                    width={512}
                    height={512}
                    src={this.state.artistImg}
                  />
                </p>
              </BpkGridColumn>
              <BpkGridColumn width={5} tabletWidth={12}>
                <p>
                  <BpkSectionList>
                    <BpkSectionListSection headerText={this.state.results.length + " songs"}>
                      {this.state.results.map(i =>
                        <BpkSectionListItem>
                          <p><b>{i[0]}</b> - <i>Popularity: {i[1]}/100</i></p>
                        </BpkSectionListItem>)}
                    </BpkSectionListSection>
                  </BpkSectionList>
                </p>
                {/*<p>*/}
                {/*  <BpkButton secondary={true} onClick={this.exportSpotify}>*/}
                {/*    Export playlist to Spotify*/}
                {/*  </BpkButton>*/}
                {/*</p>*/}
                {this.state.spotifyLink &&
                <BpkBannerAlert
                  message={`Created a Spotify playlist: ${this.state.spotifyLink}`}
                  type={ALERT_TYPES.SUCCESS}
                />}
              </BpkGridColumn>
            </BpkGridRow>
          </BpkGridContainer>
        </div>
        }
      </>);
  }
}

export default Search;
