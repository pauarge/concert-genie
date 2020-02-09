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
import BpkDrawer from "bpk-component-drawer";
import BpkBannerAlert, {ALERT_TYPES} from 'bpk-component-banner-alert';
import BpkImage from "bpk-component-image";
import Spinner from "./Spinner";
import BpkGridContainer from "bpk-component-grid/src/BpkGridContainer";
import BpkGridRow from "bpk-component-grid/src/BpkGridRow";
import BpkGridColumn from "bpk-component-grid/src/BpkGridColumn";

const doneInterval = 200;

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
      showSpinner: false,
      isDrawerOpen: false,
      drawerSong: '',
      drawerLyrics: '',
      errored: false,
    };

    this.clearSearch = this.clearSearch.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.getSuggestions = this.getSuggestions.bind(this);
  }

  clearSearch() {
    this.setState({
      value: '',
      suggestions: [],
      typingTimer: null,
      results: [],
      artistImg: null,
      showSpinner: false,
      isDrawerOpen: false,
      drawerSong: '',
      drawerLyrics: '',
      errored: false,
    });
  }

  getSuggestions(val) {
    if (this.state.value.length > 1) {
      fetch("http://localhost:5000/suggest?artist=" + val.trim())
        .then(res => res.json())
        .then(
          (result) => {
            this.setState({
              suggestions: result,
            });
          },
          error => this.setState({
            errored: true,
            showSpinner: false
          })
        )
    }
  }

  onDrawerOpen = (song) => {
    fetch("http://localhost:5000/lyrics?artist=" + this.state.value + "&song=" + song)
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            drawerSong: song,
            drawerLyrics: result,
          });
        },
        error => console.log(error)
      );

    this.setState({
      isDrawerOpen: true,
    });
  };

  onDrawerClose = () => {
    this.setState({
      isDrawerOpen: false,
    });
  };

  handleSubmit(event) {
    event.preventDefault();
    this.setState({
      results: [],
      showSpinner: true,
    }, () => {
      fetch("http://localhost:5000/?artist=" + this.state.value)
        .then(res => res.json())
        .then(
          (result) => {
            this.setState({
              results: result['playlist'],
              artistImg: result['img'],
              showSpinner: false,
              errored: false
            });
          },
          error => this.setState({
            errored: true,
            showSpinner: false
          })
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
      typingTimer: setTimeout(() => this.getSuggestions(value), doneInterval)
    });
  };

  onSuggestionsClearRequested = () => {
    this.setState({
      suggestions: [],
    });
  };

  render() {
    const {value, suggestions} = this.state;

    const inputProps = {
      id: 'my-autosuggest',
      name: 'my-autosuggest',
      placeholder: 'Start typing an artist name...',
      value,
      onChange: this.onChange,
    };

    return (
      <>
        <BpkDrawer
          id="my-drawer"
          isOpen={this.state.isDrawerOpen}
          onClose={this.onDrawerClose}
          title={this.state.drawerSong}
          closeLabel="Close drawer"
          getApplicationElement={() => document.getElementById('pagewrap')}
        >
          <div dangerouslySetInnerHTML={{__html: this.state.drawerLyrics}}/>
        </BpkDrawer>
        <form onSubmit={this.handleSubmit}>
          <p>
            <div>
              <BpkAutosuggest
                suggestions={suggestions}
                onSuggestionsFetchRequested={this.onSuggestionsFetchRequested}
                onSuggestionsClearRequested={this.onSuggestionsClearRequested}
                getSuggestionValue={getSuggestionValue}
                renderSuggestion={renderSuggestion}
                inputProps={inputProps}
              />
            </div>
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
        {this.state.errored &&
        <BpkBannerAlert
          message="Could not generate a playlist for the artist."
          type={ALERT_TYPES.ERROR}
        />
        }
        {this.state.showSpinner && <Spinner/>}
        {this.state.results.length > 0 &&
        <div>
          <p>
            <BpkButton submit={true} secondary={true}>
              Export playlist to Spotify
            </BpkButton>
          </p>
          <BpkGridContainer>
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
                <h2>Connections between songs</h2>
                <p>
                  <BpkImage
                    altText="plot"
                    width={512}
                    height={512}
                    src={"http://localhost:5000/plot.png?artist=" + this.state.value.toLowerCase()}
                  />
                </p>
              </BpkGridColumn>
              <BpkGridColumn width={5} tabletWidth={12}>
                <p>
                  <BpkSectionList>
                    <BpkSectionListSection headerText={this.state.results.length + " songs"}>
                      {this.state.results.map(i => <BpkSectionListItem
                        onClick={() => this.onDrawerOpen(i)}>{i}</BpkSectionListItem>)}
                    </BpkSectionListSection>
                  </BpkSectionList>
                </p>
              </BpkGridColumn>
            </BpkGridRow>
          </BpkGridContainer>
        </div>
        }
      </>);
  }
}

export default Search;
